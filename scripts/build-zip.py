#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the publishable CCSwitch-operations skill zip.

Packages the repository root into dist/CCSwitch-operations-<version>.zip with a
top-level CCSwitch-operations/ folder (compatible with agent skills directories
and CC Switch's import-from-zip flow).

Excluded from the zip: .git, .github, dist, __pycache__, *.pyc, .venv,
.pytest_cache, and the staging copy of the repo.
"""

import argparse
import zipfile
from pathlib import Path

TOP_LEVEL = "CCSwitch-operations"
EXCLUDE_DIRS = {".git", ".github", "dist", "__pycache__", ".venv", ".pytest_cache", "tests", "assets", "incidents"}
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_FILES = {".gitignore", "build-zip.py"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CCSwitch-operations skill zip")
    parser.add_argument("--version", default="1.1.0", help="version used in the zip filename")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out-dir", type=Path, default=None, help="defaults to <repo>/dist")
    args = parser.parse_args()

    repo = args.repo.resolve()
    out_dir = (args.out_dir or repo / "dist").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{TOP_LEVEL}-v{args.version}.zip"

    files = []
    for path in sorted(repo.rglob("*")):
        rel = path.relative_to(repo)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if (
            path.is_file()
            and path.suffix not in EXCLUDE_SUFFIXES
            and path.name not in EXCLUDE_FILES
        ):
            files.append(path)

    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arc = f"{TOP_LEVEL}/{path.relative_to(repo).as_posix()}"
            zf.write(path, arc)

    print(f"Built {out_file} with {len(files)} files")


if __name__ == "__main__":
    main()
