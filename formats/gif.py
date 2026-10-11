"""
GIF Format Helper — Job A (Normalization)
==========================================
GIF structure relevant to polyglot construction:

  Header block         GIF87a or GIF89a  (6 bytes, offset 0)
  Logical Screen Descriptor              (7 bytes)
  [Global Colour Table if present]
  ... image frames, extension blocks ...
  Trailer              0x3B              (1 byte — logical EOF)

Two versions:
  GIF87a  — original spec; extension blocks not supported
  GIF89a  — extended spec; supports Application Extension blocks,
             Plain Text Extension, Comment Extension, Graphic Control

append_tolerant: True
  GIF parsers stop at the Trailer byte (0x3B) and discard trailing data.
  All major browsers, Pillow, and giflib honour this.

has_comment_field: True (GIF89a only)
  GIF89a Comment Extension blocks (0x21 0xFE) carry arbitrary text via
  chained sub-blocks of up to 255 bytes each. Total capacity is
  effectively unlimited through sub-block chaining.
  GIF87a has no extension blocks — the comment field is unavailable.
  Job B (InjectStrategy) will handle this distinction.

Normalization goal:
  Locate the LAST 0x3B Trailer byte in the file, return bytes up to
  and including it. Trailing garbage is stripped.

Why rfind?
  In theory a GIF has exactly one Trailer, but corrupt or hand-crafted
  files may have data after the Trailer. rfind + verification is safer
  than find, and consistent with our approach across other formats.
"""

from __future__ import annotations

# ── Constants ─────────────────────────────────────────────────────────────────

GIF87A_MAGIC = b"GIF87a"
GIF89A_MAGIC = b"GIF89a"
TRAILER      = b"\x3b"


# ── Job A helpers ─────────────────────────────────────────────────────────────

def find_trailer_position(gif_bytes: bytes) -> int:
    """
    Return the byte offset immediately AFTER the GIF Trailer byte (0x3B).

    We use rfind so that the last 0x3B in the file is used. This handles
    the (rare but real) case where raw 0x3B bytes appear inside image data
    or extension blocks.

    Raises ValueError if no Trailer byte is found.
    """
    pos = gif_bytes.rfind(TRAILER)
    if pos == -1:
        raise ValueError(
            "Cannot locate GIF Trailer byte (0x3B) — is this a valid GIF?"
        )
    return pos + len(TRAILER)


def normalize(gif_bytes: bytes) -> bytes:
    """
    Trim any bytes that follow the GIF Trailer byte.

    Returns the GIF bytes up to and including 0x3B.
    No trailing newline is added — GIF is a binary format.
    """
    return gif_bytes[: find_trailer_position(gif_bytes)]


def has_valid_header(gif_bytes: bytes) -> bool:
    """
    Return True if the bytes begin with GIF87a or GIF89a magic.

    GIF has zero prepend tolerance — magic bytes must be at offset 0.
    """
    return gif_bytes[:6] in (GIF87A_MAGIC, GIF89A_MAGIC)


def is_gif89a(gif_bytes: bytes) -> bool:
    """
    Return True if this is a GIF89a file (supports extension blocks).

    Used by Job B (InjectStrategy) to determine whether Comment Extension
    blocks are available for payload injection.
    """
    return gif_bytes[:6] == GIF89A_MAGIC
