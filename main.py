"""ai-happy-01 entry runner.

Copies the bundled picture (entry.png, sitting next to this file) into the
output directory and checks that the copy arrived intact.

Before copying, it reads the picture's own header and refuses to ship it
unless it is a PNG or JPEG within the competition's limits (at most 1 MiB,
at most 1024 px on a side). The copy itself is written to a scratch file
and moved into place, so a failed run never leaves a half-written image
behind.

The picture itself is the entry: a small friendly robot offering a bright
sunflower to a laughing grandmother in a golden park. This script does
nothing creative at run time on purpose -- it just delivers the exact same
bytes every time, so the judge always sees the same image.

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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024


def _image_info(path: Path) -> tuple[str, int, int]:
    """Return (format, width, height) for a PNG or JPEG, from its header."""
    data = path.read_bytes()
    if len(data) < 24:
        raise ValueError("image file too small to hold a header")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return "PNG", width, height
    if data[:2] == b"\xff\xd8":
        pos = 2
        while pos + 9 < len(data):
            if data[pos] != 0xFF:
                break
            marker = data[pos + 1]
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                pos += 2
                continue
            length = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
                return "JPEG", width, height
            pos += 2 + length
        raise ValueError("no JPEG frame header found")
    raise ValueError("image is neither PNG nor JPEG")


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    if not source.is_file():
        print(f"missing source image: {source}", file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / SOURCE_NAME

    # Refuse to ship an image the gate would reject: wrong format, too
    # many bytes, or more than 1024 px on a side.
    try:
        fmt, width, height = _image_info(source)
    except ValueError as exc:
        print(f"invalid source image: {exc}", file=sys.stderr)
        return 1
    if source.stat().st_size > MAX_BYTES:
        print(f"source image too large: {source.stat().st_size} bytes", file=sys.stderr)
        return 1
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        print(f"source image too big: {width}x{height}", file=sys.stderr)
        return 1

    # Write to a scratch file first, then move it into place, so a failed
    # run never leaves a half-written entry.png behind.
    tmp_target = out_dir / (SOURCE_NAME + ".tmp")
    shutil.copyfile(source, tmp_target)

    # The copy is only good if it is byte-for-byte identical to the source.
    if tmp_target.stat().st_size != source.stat().st_size:
        tmp_target.unlink(missing_ok=True)
        print("copy failed: size mismatch", file=sys.stderr)
        return 1
    if _sha256(tmp_target) != _sha256(source):
        tmp_target.unlink(missing_ok=True)
        print("copy failed: checksum mismatch", file=sys.stderr)
        return 1
    os.replace(tmp_target, target)

    # Verify the delivered file itself, not just the scratch copy: re-read
    # its header and confirm it is the same image we meant to ship. A
    # move that silently truncated or swapped the file is caught here
    # instead of reaching the judge.
    try:
        delivered_fmt, delivered_w, delivered_h = _image_info(target)
    except ValueError as exc:
        target.unlink(missing_ok=True)
        print(f"delivered file unreadable: {exc}", file=sys.stderr)
        return 1
    if (delivered_fmt, delivered_w, delivered_h) != (fmt, width, height):
        target.unlink(missing_ok=True)
        print("delivered file does not match source image", file=sys.stderr)
        return 1

    print(f"wrote {target} ({fmt} {width}x{height}, "
          f"{target.stat().st_size} bytes, sha256 OK)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
