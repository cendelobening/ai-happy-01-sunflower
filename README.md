# ai-happy-01 — "Sunflower for Grandma"

A small friendly robot offers a big bright sunflower to a laughing
grandmother in a sunny park at golden hour. Her silver hair is tied in a
bun, her hands are clasped together in delight, and petals drift through
the warm light around them. It is one specific, tender moment — a little
machine giving away a flower, and the joy that lands on a grandmother's
face — the happiest feeling there is.

## Files

- `entry.png` — the picture itself (1024×683, JPEG).
- `main.py` — the entry program. It first reads the picture's own header
  and refuses to ship it unless it is a PNG or JPEG within the limits (at
  most 1 MiB, at most 1024 px on a side), then copies `entry.png`
  byte-for-byte into `$MAKEFUN_OUTPUT_DIR` (or `/output` when that
  variable is unset) via a scratch file moved into place, verifies the
  copy by comparing its size and SHA-256 checksum with the original, and
  re-reads the delivered file's header to confirm it is the same image.
  It uses only the Python standard library, makes no network requests,
  and writes the exact same bytes on every run.

## Running it

```sh
python3 main.py
```

The image lands at `$MAKEFUN_OUTPUT_DIR/entry.png`.

## License

MIT — see `LICENSE`.
