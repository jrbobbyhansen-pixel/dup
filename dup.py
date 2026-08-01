#!/usr/bin/env python3
"""dup — Duplicate file finder by content hash (SHA-256).

Scan directories, find duplicate files by content hash, and list groups
of duplicates. Zero external dependencies — uses only stdlib.
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict

__version__ = "1.0.0"
PROGRAM = "dup"


def sha256sum(path: str, blocksize: int = 65536) -> str:
    """Compute SHA-256 hex digest of a file, reading in fixed-size blocks."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                block = f.read(blocksize)
                if not block:
                    break
                h.update(block)
    except PermissionError:
        raise PermissionError(f"Permission denied: {path}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except IsADirectoryError:
        raise IsADirectoryError(f"Expected a file, got a directory: {path}")
    except OSError as e:
        raise OSError(f"Error reading {path}: {e}")
    return h.hexdigest()


def scan_directory(root: str, follow_symlinks: bool = False) -> list[str]:
    """Recursively walk *root* and return paths to regular files."""
    files: list[str] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
            for name in filenames:
                path = os.path.join(dirpath, name)
                try:
                    if os.path.isfile(path):
                        files.append(path)
                except OSError:
                    continue
    except PermissionError:
        raise PermissionError(f"Permission denied while scanning: {root}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Directory not found: {root}")
    return files


def find_duplicates(
    paths: list[str], follow_symlinks: bool = False, quiet: bool = False
) -> dict[str, list[str]]:
    """Return a dict mapping content hash -> list of duplicate file paths.

    Only hashes with 2+ files are included.
    """
    hash_map: dict[str, list[str]] = defaultdict(list)

    for path in paths:
        if not os.path.exists(path):
            print(f"Warning: path does not exist, skipping: {path}", file=sys.stderr)
            continue

        if os.path.isdir(path):
            files = scan_directory(path, follow_symlinks=follow_symlinks)
        elif os.path.isfile(path):
            files = [path]
        else:
            print(f"Warning: not a file or directory, skipping: {path}", file=sys.stderr)
            continue

        for fpath in files:
            if not quiet:
                print(f"  Hashing: {fpath}", file=sys.stderr)
            try:
                digest = sha256sum(fpath)
                hash_map[digest].append(fpath)
            except (PermissionError, OSError, FileNotFoundError) as e:
                print(f"Warning: {e}", file=sys.stderr)
                continue

    # Filter to only duplicates (2+ files with same hash)
    return {h: paths for h, paths in hash_map.items() if len(paths) >= 2}


def format_size(nbytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def print_duplicates(dupes: dict[str, list[str]], show_size: bool = False) -> None:
    """Print duplicate groups to stdout."""
    if not dupes:
        print("No duplicates found.")
        return

    total_dupes = sum(len(paths) - 1 for paths in dupes.values())
    total_wasted = 0

    print(f"\nFound {len(dupes)} group(s) of duplicates ({total_dupes} redundant files):\n")

    for i, (digest, paths) in enumerate(dupes.items(), 1):
        # Get size from the first file
        size_str = ""
        wasted = 0
        if show_size:
            try:
                size = os.path.getsize(paths[0])
                wasted = size * (len(paths) - 1)
                total_wasted += wasted
                size_str = f"  [{format_size(size)} each]"
            except OSError:
                pass

        print(f"  Group {i}: {digest}{size_str}")
        for p in paths:
            print(f"    {p}")
        print()

    if show_size and total_wasted > 0:
        print(f"Total wasted space: {format_size(total_wasted)}")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Find duplicate files by content hash (SHA-256).",
        epilog=(
            "Examples:\n"
            f"  {PROGRAM} ~/Documents\n"
            f"  {PROGRAM} ~/Pictures ~/Downloads --size\n"
            f"  {PROGRAM} . --quiet\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more files or directories to scan",
    )
    parser.add_argument(
        "-s", "--size",
        action="store_true",
        help="Show file sizes and total wasted space",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output (hashing status)",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links when scanning directories",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"{PROGRAM} {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        dupes = find_duplicates(
            args.paths,
            follow_symlinks=args.follow_symlinks,
            quiet=args.quiet,
        )
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print_duplicates(dupes, show_size=args.size)
    return 0 if not dupes else 1


if __name__ == "__main__":
    sys.exit(main())
