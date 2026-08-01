# dup — Duplicate File Finder

Scan directories, find duplicate files by content hash (SHA-256), and list groups of duplicates. Zero external dependencies — uses only Python stdlib (`os`, `hashlib`, `argparse`, `collections`). Portable across macOS, Linux, and WSL.

## Install

```bash
pip install git+https://github.com/jrbobbyhansen-pixel/dup.git
```

Or just copy `dup.py` anywhere on your `PATH`:

```bash
curl -O https://raw.githubusercontent.com/jrbobbyhansen-pixel/dup/main/dup.py
chmod +x dup.py
```

## Usage

```bash
# Scan a directory
dup ~/Documents

# Scan multiple paths, show file sizes and wasted space
dup ~/Pictures ~/Downloads --size

# Quiet mode (no per-file hashing progress)
dup . --quiet

# Show version
dup --version
```

Exit code: `0` if no duplicates found, `1` if duplicates were found.

## Test

```bash
pip install pytest
pytest -v
```

## License

MIT — see [LICENSE](LICENSE).

---

Part of the [Manta](https://github.com/jrbobbyhansen-pixel) collection — zero-dependency CLI tools for developers.
