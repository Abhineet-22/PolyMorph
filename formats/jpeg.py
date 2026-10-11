"""
JPEG Format Helper — Job A (Normalization)
==========================================
JPEG structure relevant to polyglot construction:

  SOI  FF D8          — Start of Image (magic bytes, must be at offset 0)
  ...  marker segments (FF XX LL LL data)
  EOI  FF D9          — End of Image (logical EOF)

append_tolerant: True
  JPEG parsers stop at EOI and discard everything after it.
  Any bytes appended after FF D9 are invisible to the JPEG decoder.

Normalization goal:
  Locate the LAST FF D9 in the file, return bytes up to and including
  that marker. Trailing garbage (from a previous construction attempt,
  test artifact, or unknown origin) is stripped.

Why rfind, not find?
  Some JPEG files embed thumbnail images in EXIF APP1 segments that
  themselves contain a complete SOI/EOI pair. rfind ensures we stop at
  the outermost EOI, not an inner thumbnail's EOI.
"""

from __future__ import annotations

# ── Constants ─────────────────────────────────────────────────────────────────

SOI_MARKER = b"\xff\xd8"        # Start of Image — must be at offset 0
EOI_MARKER = b"\xff\xd9"        # End of Image   — logical EOF
JPEG_MAGIC  = b"\xff\xd8\xff"   # First 3 bytes of every valid JPEG


# ── Job A helpers ─────────────────────────────────────────────────────────────

def find_eoi_position(jpeg_bytes: bytes) -> int:
    """
    Return the byte offset immediately AFTER the last FF D9 EOI marker.

    We use rfind (last occurrence) rather than find (first occurrence)
    because embedded EXIF thumbnails contain their own SOI/EOI pair earlier
    in the stream. Using the last FF D9 ensures we capture the outermost image.

    Raises ValueError if no FF D9 is found.
    """
    pos = jpeg_bytes.rfind(EOI_MARKER)
    if pos == -1:
        raise ValueError(
            "Cannot locate EOI marker (FF D9) — is this a valid JPEG?"
        )
    return pos + len(EOI_MARKER)


def normalize(jpeg_bytes: bytes) -> bytes:
    """
    Trim any bytes that follow the last FF D9 EOI marker.

    Returns the JPEG bytes up to and including the EOI.
    No trailing newline is added (unlike PDF) because JPEG is a binary
    format and inserting text bytes after the EOI would be detectable.
    """
    return jpeg_bytes[: find_eoi_position(jpeg_bytes)]


def has_valid_header(jpeg_bytes: bytes) -> bool:
    """
    Return True if the bytes begin with the JPEG SOI magic sequence FF D8 FF.

    JPEG has zero prepend tolerance — the magic bytes must be at offset 0.
    """
    return jpeg_bytes[:3] == JPEG_MAGIC
