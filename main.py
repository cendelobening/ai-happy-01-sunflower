"""ai-happy-01 entry runner.

Delivers the bundled picture (entry.png, next to this file) to the output
directory, and proves the delivery arrived intact.

The picture is the entry: a small robot offering a sunflower to a laughing
grandmother in a golden park. The program itself is deliberately boring --
it ships the exact same bytes on every run, so the judge always sees the
same image.

What it does, in order:
  1. Reads the picture's header and refuses anything that is not a PNG or
     JPEG inside the competition's limits (1 MiB, 1024 px a side).
  2. Copies the picture to a scratch file, checks the copy byte for byte,
     then moves it into place -- a failed run never leaves a half-written
     entry.png behind.
  3. Reads the delivered file's header back and confirms it is the same
     picture that was meant to be shipped.

Usage: python3 main.py
Output: $MAKEFUN_OUTPUT_DIR/entry.png (falls back to /output/entry.png)
"""

import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

SOURCE_NAME = "entry.png"
MAX_BYTES = 1_048_576
MAX_SIDE = 1024


def _file_sha256(path):
    """SHA-256 of a file, streamed so big files stay cheap."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_image_header(path):
    """(format, width, height) for a PNG or JPEG, parsed from its header."""
    data = path.read_bytes()
    if len(data) < 24:
        raise ValueError("file too small to hold an image header")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return "PNG", width, height
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a PNG or JPEG image")
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            break
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return "JPEG", width, height
        pos += 2 + length
    raise ValueError("no JPEG frame header found")


def _check_source(source):
    """Read and gate the source picture; return (format, width, height)."""
    if not source.is_file():
        raise ValueError(f"missing source image: {source}")
    fmt, width, height = _read_image_header(source)
    size = source.stat().st_size
    if size > MAX_BYTES:
        raise ValueError(f"source image too large: {size} bytes")
    if width > MAX_SIDE or height > MAX_SIDE:
        raise ValueError(f"source image too big: {width}x{height}")
    return fmt, width, height


def _deliver(source, target, fmt, width, height):
    """Copy source to target atomically, verifying every step."""
    tmp_target = target.with_name(target.name + ".tmp")
    # A stale scratch file from an interrupted earlier run must not linger:
    # start clean so a half-written leftover can never be mistaken for a
    # fresh copy.
    tmp_target.unlink(missing_ok=True)
    shutil.copyfile(source, tmp_target)
    if tmp_target.stat().st_size != source.stat().st_size:
        tmp_target.unlink(missing_ok=True)
        raise ValueError("copy failed: size mismatch")
    if _file_sha256(tmp_target) != _file_sha256(source):
        tmp_target.unlink(missing_ok=True)
        raise ValueError("copy failed: checksum mismatch")
    os.replace(tmp_target, target)
    delivered = _read_image_header(target)
    if delivered != (fmt, width, height):
        target.unlink(missing_ok=True)
        raise ValueError("delivered file does not match source image")


def main():
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / SOURCE_NAME
    try:
        fmt, width, height = _check_source(source)
        _deliver(source, target, fmt, width, height)
    except ValueError as exc:
        print(f"entry refused: {exc}", file=sys.stderr)
        return 1
    print(f"delivered {target} ({fmt} {width}x{height}, "
          f"{target.stat().st_size} bytes, sha256 OK)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
