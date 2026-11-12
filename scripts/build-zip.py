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
import re
import zipfile
from pathlib import Path

TOP_LEVEL = "CCSwitch-operations"
SKILL_NAME = "ccswitch-operations"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXCLUDE_DIRS = {".git", ".github", "dist", "__pycache__", ".venv", ".pytest_cache", "tests", "assets", "incidents"}
EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_FILES = {".gitignore", "build-zip.py"}


def validate_skill(repo: Path) -> None:
    skill_md = repo / "SKILL.md"
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read SKILL.md: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc

    fields = {}
    for line in lines[1:end]:
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        fields[key.strip()] = value

    name = fields.get("name", "")
    description = fields.get("description", "").strip()
    if not name:
        raise ValueError("SKILL.md frontmatter requires name")
    if not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(f"skill name {name!r} is not lowercase kebab-case")
    if name != SKILL_NAME:
        raise ValueError(f"skill name must be {SKILL_NAME!r}, got {name!r}")
    if not description:
        raise ValueError("SKILL.md frontmatter requires description")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the CCSwitch-operations skill zip")
    parser.add_argument("--version", default="1.5.3", help="version used in the zip filename")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out-dir", type=Path, default=None, help="defaults to <repo>/dist")
    args = parser.parse_args()

    repo = args.repo.resolve()
    try:
        validate_skill(repo)
    except ValueError as exc:
        parser.exit(1, f"error: {exc}\n")
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
