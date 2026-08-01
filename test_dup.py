"""Tests for dup — duplicate file finder."""

import hashlib
import os
import sys
import tempfile

import pytest

# Ensure the module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dup


# ---------------------------------------------------------------------------
# sha256sum
# ---------------------------------------------------------------------------

def test_sha256sum_known_content():
    """SHA-256 of known content matches expected."""
    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as f:
        f.write(b"hello world\n")
        tmp = f.name
    try:
        digest = dup.sha256sum(tmp)
        # echo -n "hello world\n" | sha256sum
        expected = "a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447"
        assert digest == expected
    finally:
        os.unlink(tmp)


def test_sha256sum_empty_file():
    """SHA-256 of empty file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        tmp = f.name
    try:
        digest = dup.sha256sum(tmp)
        assert digest == hashlib.sha256(b"").hexdigest()
    finally:
        os.unlink(tmp)


def test_sha256sum_missing_file():
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        dup.sha256sum("/tmp/nonexistent-file-xyz-123")


def test_sha256sum_directory():
    """Directory raises IsADirectoryError."""
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(IsADirectoryError):
            dup.sha256sum(d)


# ---------------------------------------------------------------------------
# scan_directory
# ---------------------------------------------------------------------------

def test_scan_directory_flat():
    """Scan a flat directory with a few files."""
    with tempfile.TemporaryDirectory() as d:
        for name in ("a.txt", "b.txt", "c.txt"):
            open(os.path.join(d, name), "w").close()
        files = dup.scan_directory(d)
        assert len(files) == 3
        assert all(f.startswith(d) for f in files)


def test_scan_directory_nested():
    """Scan a nested directory tree."""
    with tempfile.TemporaryDirectory() as d:
        sub = os.path.join(d, "sub")
        os.mkdir(sub)
        open(os.path.join(d, "root.txt"), "w").close()
        open(os.path.join(sub, "nested.txt"), "w").close()
        files = dup.scan_directory(d)
        assert len(files) == 2


def test_scan_directory_missing():
    """Missing directory returns empty list (os.walk doesn't raise)."""
    files = dup.scan_directory("/tmp/nonexistent-dir-xyz-123")
    assert files == []


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_find_duplicates_identical_files():
    """Two identical files are reported as duplicates."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt")
        b = os.path.join(d, "b.txt")
        with open(a, "w") as f:
            f.write("same content")
        with open(b, "w") as f:
            f.write("same content")
        result = dup.find_duplicates([d], quiet=True)
        assert len(result) == 1
        paths = list(result.values())[0]
        assert len(paths) == 2
        assert a in paths
        assert b in paths


def test_find_duplicates_unique_files():
    """Files with different content produce no duplicates."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt")
        b = os.path.join(d, "b.txt")
        with open(a, "w") as f:
            f.write("content A")
        with open(b, "w") as f:
            f.write("content B")
        result = dup.find_duplicates([d], quiet=True)
        assert len(result) == 0


def test_find_duplicates_single_file():
    """A single file produces no duplicates."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt")
        with open(a, "w") as f:
            f.write("content")
        result = dup.find_duplicates([d], quiet=True)
        assert len(result) == 0


def test_find_duplicates_missing_path():
    """Missing path produces a warning but no crash."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt")
        with open(a, "w") as f:
            f.write("content")
        result = dup.find_duplicates([d, "/tmp/nonexistent-path-xyz"], quiet=True)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# format_size
# ---------------------------------------------------------------------------

def test_format_size_bytes():
    assert dup.format_size(0) == "0.0 B"
    assert dup.format_size(512) == "512.0 B"
    assert dup.format_size(1023) == "1023.0 B"


def test_format_size_kb():
    assert dup.format_size(1024) == "1.0 KB"
    assert dup.format_size(2048) == "2.0 KB"


def test_format_size_mb():
    assert dup.format_size(1048576) == "1.0 MB"


def test_format_size_gb():
    assert dup.format_size(1073741824) == "1.0 GB"


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def test_cli_version():
    """--version prints version string and exits 0."""
    with pytest.raises(SystemExit) as exc:
        dup.main(["--version"])
    assert exc.value.code == 0


def test_cli_help():
    """--help prints help and exits 0."""
    with pytest.raises(SystemExit) as exc:
        dup.main(["--help"])
    assert exc.value.code == 0


def test_cli_no_duplicates():
    """Scan a dir with unique files exits 0."""
    with tempfile.TemporaryDirectory() as d:
        for name in ("x.txt", "y.txt"):
            with open(os.path.join(d, name), "w") as f:
                f.write(name)
        rc = dup.main([d, "--quiet"])
        assert rc == 0


def test_cli_with_duplicates():
    """Scan a dir with duplicates exits 1."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt")
        b = os.path.join(d, "b.txt")
        with open(a, "w") as f:
            f.write("same")
        with open(b, "w") as f:
            f.write("same")
        rc = dup.main([d, "--quiet"])
        assert rc == 1


def test_cli_missing_dir():
    """Missing directory exits 0 (gracefully handled, no duplicates)."""
    rc = dup.main(["/tmp/nonexistent-dir-xyz-123", "--quiet"])
    assert rc == 0


def test_cli_size_flag():
    """--size flag does not crash."""
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt")
        b = os.path.join(d, "b.txt")
        with open(a, "w") as f:
            f.write("same")
        with open(b, "w") as f:
            f.write("same")
        rc = dup.main([d, "--quiet", "--size"])
        assert rc == 1


# ---------------------------------------------------------------------------
# main() with no args
# ---------------------------------------------------------------------------

def test_cli_no_args():
    """No args prints usage and exits 2."""
    with pytest.raises(SystemExit) as exc:
        dup.main([])
    assert exc.value.code == 2
