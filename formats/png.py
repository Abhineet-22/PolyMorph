"""
PNG Format Helper — Job A (Normalization)
==========================================
PNG structure relevant to polyglot construction:

  8-byte signature  89 50 4E 47 0D 0A 1A 0A  (\x89PNG\r\n\x1a\n)
  IHDR chunk        image dimensions, bit depth, colour type
  ... ancillary and critical chunks ...
  IEND chunk        always the LAST chunk; marks logical EOF

Each chunk layout:
  4 bytes  — data length (big-endian uint32)
  4 bytes  — chunk type  (ASCII: IHDR, IDAT, IEND, tEXt …)
  N bytes  — chunk data  (N = data length)
  4 bytes  — CRC32 over type + data

IEND is always 12 bytes:
  \x00\x00\x00\x00  (length = 0, no data)
  IEND              (type)
  \xae\x42\x60\x82 (CRC32 of "IEND" with no data — a fixed constant)

append_tolerant: True
  The PNG spec states parsers MUST stop at IEND and ignore subsequent
  bytes. Libpng, Pillow, and all major browsers honour this.

has_internal_checksum: True (per chunk, NOT file-level)
  Each chunk has its own CRC32. Appending after IEND does not affect
  any chunk CRC — the appended bytes are outside every chunk boundary.
  checksum_covers_append is therefore False.

Normalization goal:
  Locate the IEND chunk, return bytes up to and including it (all 12 bytes).
"""

from __future__ import annotations
import struct

# ── Constants ─────────────────────────────────────────────────────────────────

PNG_SIGNATURE  = b"\x89PNG\r\n\x1a\n"    # 8-byte PNG magic (offset 0)
IEND_TYPE      = b"IEND"
IEND_CRC       = b"\xae\x42\x60\x82"     # CRC32("IEND") with zero data

# A complete IEND chunk is always these exact 12 bytes.
IEND_CHUNK     = b"\x00\x00\x00\x00" + IEND_TYPE + IEND_CRC


# ── Job A helpers ─────────────────────────────────────────────────────────────

def find_iend_position(png_bytes: bytes) -> int:
    """
    Return the byte offset immediately AFTER the IEND chunk.

    We search for the complete 12-byte IEND chunk sequence
    (b"\\x00\\x00\\x00\\x00IEND\\xae\\x42\\x60\\x82") rather than just the
    4-byte type field. This prevents false matches when the literal string
    "IEND" appears in appended garbage bytes or embedded text metadata.

    Returns: offset of the first byte after the IEND chunk (i.e. chunk_start + 12).

    Raises ValueError if the complete IEND chunk is not found.
    """
    pos = png_bytes.rfind(IEND_CHUNK)
    if pos == -1:
        raise ValueError(
            "Cannot locate IEND chunk — is this a valid PNG? "
            "(Searched for complete 12-byte IEND chunk: "
            "00 00 00 00 49 45 4E 44 AE 42 60 82)"
        )
    # pos is the start of the 12-byte IEND chunk.
    return pos + len(IEND_CHUNK)   # = pos + 12


def normalize(png_bytes: bytes) -> bytes:
    """
    Return PNG bytes up to and including the IEND chunk, trimming
    any data that follows it.

    No trailing newline is added — PNG is purely binary.
    """
    return png_bytes[: find_iend_position(png_bytes)]


def has_valid_header(png_bytes: bytes) -> bool:
    """
    Return True if the bytes begin with the 8-byte PNG signature.

    PNG has zero prepend tolerance — the signature must be at offset 0.
    """
    return png_bytes[:8] == PNG_SIGNATURE
