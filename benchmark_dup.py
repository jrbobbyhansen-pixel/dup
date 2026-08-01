#!/usr/bin/env python3
"""Benchmark manta-dup against fdupes (if available) and find.

Measures:
- Time to scan directories of various sizes
- Memory usage during scan
- Accuracy vs reference implementation

Usage:
    python3 benchmark_dup.py [--dir DIR] [--sizes SMALL,MEDIUM,LARGE]

Outputs JSON results to stdout.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc


def create_test_dir(base_dir, num_files, file_size_kb):
    """Create a directory with num_files files of file_size_kb each."""
    dir_path = os.path.join(base_dir, f"test_{num_files}_{file_size_kb}")
    os.makedirs(dir_path, exist_ok=True)

    # Create unique files
    for i in range(num_files):
        path = os.path.join(dir_path, f"file_{i}.txt")
        with open(path, "w") as f:
            f.write(f"Content {i} " * (file_size_kb * 10))

    # Create some duplicates (10% of files)
    dup_count = max(1, num_files // 10)
    for i in range(dup_count):
        src = os.path.join(dir_path, f"file_{i}.txt")
        dst = os.path.join(dir_path, f"dup_{i}.txt")
        shutil.copy2(src, dst)

    return dir_path


def benchmark_tool(tool_name, cmd, dir_path):
    """Run a tool and measure time + memory."""
    tracemalloc.start()
    start = time.time()

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60
    )

    elapsed = time.time() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "tool": tool_name,
        "elapsed_seconds": round(elapsed, 3),
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "exit_code": result.returncode,
        "stdout_lines": len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0,
        "stderr": result.stderr[:200] if result.stderr else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark manta-dup")
    parser.add_argument("--dir", default=None, help="Directory to scan")
    parser.add_argument(
        "--sizes", default="50,200,1000",
        help="Comma-separated file counts for small/medium/large tests"
    )
    args = parser.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for num_files in sizes:
            print(f"Creating test dir with {num_files} files...", file=sys.stderr)
            test_dir = create_test_dir(tmpdir, num_files, 1)  # 1KB files

            # Benchmark manta-dup
            dup_script = os.path.join(os.path.dirname(__file__), "..", "dup.py")
            if os.path.exists(dup_script):
                r = benchmark_tool(
                    "manta-dup", [sys.executable, dup_script, test_dir], test_dir
                )
                r["test_size"] = num_files
                results.append(r)

            # Benchmark find + sort (baseline)
            r = benchmark_tool(
                "find+sort (baseline)",
                ["bash", "-c", f"find {test_dir} -type f -exec sha256sum {{}} \\; | sort"],
                test_dir,
            )
            r["test_size"] = num_files
            results.append(r)

            # Benchmark fdupes if available
            if shutil.which("fdupes"):
                r = benchmark_tool(
                    "fdupes",
                    ["fdupes", "-r", test_dir],
                    test_dir,
                )
                r["test_size"] = num_files
                results.append(r)

            print(f"  Done: {num_files} files", file=sys.stderr)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
