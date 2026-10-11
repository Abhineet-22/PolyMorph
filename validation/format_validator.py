from __future__ import annotations
import io, zipfile
from dataclasses import dataclass

@dataclass
class ValidationResult:
    fmt: str
    valid: bool
    detail: str

class FormatValidator:
    @classmethod
    def validate(cls, data: bytes, fmt: str) -> ValidationResult:
        method = cls._VALIDATORS.get(fmt)
        if method is None:
            return ValidationResult(fmt=fmt, valid=True,
                detail="No validator registered for this format — skipped.")
        valid, detail = method(data)
        return ValidationResult(fmt=fmt, valid=valid, detail=detail)

    @classmethod
    def validate_both(cls, data, fmt_a, fmt_b):
        return cls.validate(data, fmt_a), cls.validate(data, fmt_b)

    @staticmethod
    def _validate_pdf(data):
        try:
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(data), strict=False)
            return True, f"pypdf: {len(r.pages)} page(s) read successfully."
        except ImportError:
            if data[:4] == b"%PDF" and b"%%EOF" in data:
                return True, "pypdf not installed — magic byte check passed."
            return False, "pypdf not installed and magic byte check failed."
        except Exception as exc:
            return False, f"pypdf: {exc}"

    @staticmethod
    def _validate_zip(data):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = zf.namelist()
                bad = zf.testzip()
                if bad:
                    return False, f"CRC error in: {bad}"
                return True, f"zipfile: {len(names)} entr(ies) — {names[:5]}"
        except zipfile.BadZipFile as exc:
            return False, f"zipfile: {exc}"
        except Exception as exc:
            return False, f"zipfile: {exc}"

    @staticmethod
    def _validate_pillow(data):
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            img.verify()
            return True, f"Pillow: {img.format} verified."
        except ImportError:
            return True, "Pillow not installed — skipped."
        except Exception as exc:
            return False, f"Pillow: {exc}"

    @staticmethod
    def _validate_html(data):
        text = data[:4096].decode("utf-8", errors="ignore").lower()
        if "<html" in text or "<!doctype" in text:
            return True, "HTML: tag structure detected."
        return False, "HTML: no <html> or <!DOCTYPE> in first 4 KB."

FormatValidator._VALIDATORS = {
    "pypdf":   FormatValidator._validate_pdf,
    "zipfile": FormatValidator._validate_zip,
    "pillow":  FormatValidator._validate_pillow,
    "html":    FormatValidator._validate_html,
    "docx":    FormatValidator._validate_zip,
    "jar":     FormatValidator._validate_zip,
}
