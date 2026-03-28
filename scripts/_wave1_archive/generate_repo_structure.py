#!/usr/bin/env python3
"""Generate a readable repository tree file (repo_structure.txt by default)."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".conda",
    ".dvc_storage",
    ".mypy_cache",
    ".pytest_cache",
    ".qodo",
    "__pycache__",
}

DEFAULT_EXCLUDE_FILES = {
    "texput.log",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate repository structure as an ASCII tree."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root path (default: project root).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("repo_structure.txt"),
        help="Output file path (default: repo_structure.txt).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help=(
            "Maximum depth relative to root. "
            "0 prints only root, 1 includes root children, 2 includes grandchildren. "
            "Use -1 for unlimited depth."
        ),
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files/directories (names starting with '.').",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude-file",
        action="append",
        default=[],
        help="File name to exclude. Can be used multiple times.",
    )
    parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Do not apply built-in excludes (shows everything except the output file itself).",
    )
    return parser.parse_args()


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def should_skip(path: Path, include_hidden: bool, exclude_dirs: set[str], exclude_files: set[str]) -> bool:
    if not include_hidden and is_hidden(path):
        return True
    if path.is_dir() and path.name in exclude_dirs:
        return True
    if path.is_file() and path.name in exclude_files:
        return True
    return False


def list_children(path: Path, include_hidden: bool, exclude_dirs: set[str], exclude_files: set[str]) -> list[Path]:
    children = []
    for child in path.iterdir():
        if should_skip(child, include_hidden, exclude_dirs, exclude_files):
            continue
        children.append(child)
    return sorted(children, key=lambda p: (not p.is_dir(), p.name.lower()))


def build_tree(
    root: Path,
    max_depth: int,
    include_hidden: bool,
    exclude_dirs: set[str],
    exclude_files: set[str],
) -> list[str]:
    lines = [f"{root.name}/"]

    def walk(current: Path, prefix: str, depth: int) -> None:
        if max_depth >= 0 and depth >= max_depth:
            return

        children = list_children(current, include_hidden, exclude_dirs, exclude_files)
        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            branch = "`-- " if is_last else "|-- "
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{prefix}{branch}{child.name}{suffix}")

            if child.is_dir():
                next_prefix = prefix + ("    " if is_last else "|   ")
                walk(child, next_prefix, depth + 1)

    walk(root, "", 0)
    return lines


def main() -> int:
    args = parse_args()

    root = args.root.resolve()
    output = args.output
    if not output.is_absolute():
        output = root / output

    if args.no_default_excludes:
        exclude_dirs: set[str] = set()
        exclude_files: set[str] = set()
    else:
        exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
        exclude_files = set(DEFAULT_EXCLUDE_FILES)

    exclude_dirs.update(args.exclude_dir)
    exclude_files.update(args.exclude_file)

    # Prevent self-inclusion noise if output is inside the root.
    exclude_files.add(output.name)

    lines = build_tree(
        root=root,
        max_depth=args.max_depth,
        include_hidden=args.include_hidden,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
    )

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
