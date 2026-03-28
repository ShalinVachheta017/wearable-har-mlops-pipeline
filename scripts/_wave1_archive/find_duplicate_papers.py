#!/usr/bin/env python3
"""
find_duplicate_papers.py
─────────────────────────────────────────────────────────────────────────────
Detects duplicate PDF files across:
  - archive/          (all subfolders)
  - thesis/refs/papers_all/  (all subfolders)

Detection strategy
  1. Exact duplicates  — identical SHA-256 hash (same file content)
  2. Name collisions   — same filename, different hash (potential confusion)

SAFETY: This script NEVER deletes, moves, or renames any file.

Outputs (both written to reports/repo_audit/):
  ARCHIVE_DUPLICATES_REPORT.md  — human-readable Markdown report
  ARCHIVE_DUPLICATES.csv        — machine-readable flat table

Usage:
  python scripts/find_duplicate_papers.py [--root <project_root>]
"""

import argparse
import csv
import hashlib
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
SCAN_DIRS_REL = [
    "archive",
    "thesis/refs/papers_all",
]
OUTPUT_DIR_REL = "reports/repo_audit"
REPORT_MD = "ARCHIVE_DUPLICATES_REPORT.md"
REPORT_CSV = "ARCHIVE_DUPLICATES.csv"
CHUNK = 65536  # read chunk for hashing


# ── Helpers ───────────────────────────────────────────────────────────────────
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def collect_pdfs(roots: list[Path]) -> list[Path]:
    pdfs = []
    for root in roots:
        if not root.exists():
            print(f"  [WARN] Scan directory not found, skipping: {root}", file=sys.stderr)
            continue
        for p in root.rglob("*.pdf"):
            if p.is_file():
                pdfs.append(p)
    return sorted(pdfs)


def in_archive(path: Path, project_root: Path) -> bool:
    try:
        rel = path.relative_to(project_root)
        return rel.parts[0] == "archive"
    except ValueError:
        return False


def in_thesis(path: Path, project_root: Path) -> bool:
    try:
        rel = path.relative_to(project_root)
        return rel.parts[0] == "thesis"
    except ValueError:
        return False


# ── Core logic ────────────────────────────────────────────────────────────────
def build_index(pdfs: list[Path]) -> tuple[dict, dict]:
    """
    Returns:
      hash_map  : {sha256_hex: [Path, ...]}
      name_map  : {filename: [Path, ...]}
    """
    hash_map: dict[str, list[Path]] = defaultdict(list)
    name_map: dict[str, list[Path]] = defaultdict(list)
    total = len(pdfs)
    for i, p in enumerate(pdfs, 1):
        if i % 50 == 0 or i == total:
            print(f"  Hashing {i}/{total} …", end="\r")
        try:
            h = sha256(p)
            hash_map[h].append(p)
            name_map[p.name].append(p)
        except (OSError, PermissionError) as exc:
            print(f"\n  [WARN] Cannot read {p}: {exc}", file=sys.stderr)
    print()
    return dict(hash_map), dict(name_map)


def exact_duplicate_groups(hash_map: dict) -> list[dict]:
    """Return duplicate groups sorted by duplicate count descending."""
    groups = []
    for h, paths in hash_map.items():
        if len(paths) < 2:
            continue
        size = paths[0].stat().st_size
        groups.append(
            {
                "hash": h,
                "count": len(paths),
                "size_bytes": size,
                "paths": sorted(str(p) for p in paths),
                "filenames": sorted(set(p.name for p in paths)),
            }
        )
    return sorted(groups, key=lambda g: g["count"], reverse=True)


def cross_tree_groups(exact_groups: list[dict], project_root: Path) -> list[dict]:
    """Subset of exact_groups where at least one path is in archive/ AND one in thesis/."""
    cross = []
    for g in exact_groups:
        paths = [Path(p) for p in g["paths"]]
        has_archive = any(in_archive(p, project_root) for p in paths)
        has_thesis = any(in_thesis(p, project_root) for p in paths)
        if has_archive and has_thesis:
            cross.append(g)
    return cross


def name_collision_groups(name_map: dict) -> list[dict]:
    """Files with the same filename but different hashes."""
    collisions = []
    for name, paths in name_map.items():
        if len(paths) < 2:
            continue
        # Group by hash
        by_hash: dict[str, list[Path]] = defaultdict(list)
        for p in paths:
            try:
                h = sha256(p)
                by_hash[h].append(p)
            except (OSError, PermissionError):
                pass
        if len(by_hash) > 1:
            collisions.append(
                {
                    "filename": name,
                    "variants": [
                        {
                            "hash": h,
                            "paths": sorted(str(p) for p in ps),
                            "size_bytes": ps[0].stat().st_size,
                        }
                        for h, ps in sorted(by_hash.items())
                    ],
                }
            )
    return sorted(collisions, key=lambda c: c["filename"])


# ── Recommendation helper ─────────────────────────────────────────────────────
def recommendation(group: dict, cross: bool) -> str:
    if cross:
        return (
            "Cross-tree duplicate: keep thesis/refs/papers_all/ copy as canonical; "
            "review archive/ copy before any removal."
        )
    paths = group["paths"]
    archive_paths = [p for p in paths if "archive" + os.sep in p or "archive/" in p]
    thesis_paths = [p for p in paths if "thesis" + os.sep in p or "thesis/" in p]
    if archive_paths and not thesis_paths:
        return "All copies inside archive/ — mark for consolidation during archive cleanup."
    return "Review all copies; keep the most recently accessed or canonical version."


# ── Writers ───────────────────────────────────────────────────────────────────
def _fmt_size(b: int) -> str:
    if b >= 1_048_576:
        return f"{b / 1_048_576:.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"


def write_markdown(
    output_path: Path,
    exact_groups: list[dict],
    cross_groups: list[dict],
    name_collisions: list[dict],
    total_pdfs: int,
    scan_dirs: list[Path],
    project_root: Path,
    ts: str,
) -> None:
    cross_hashes = {g["hash"] for g in cross_groups}

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Archive Duplicate Papers Report\n\n")
        f.write(f"**Generated:** {ts}  \n")
        f.write(f"**Branch:** chore/repo-cleanup  \n")
        f.write(f"**Total PDFs scanned:** {total_pdfs}  \n")
        f.write(f"**Scanned directories:**\n")
        for d in scan_dirs:
            rel = d.relative_to(project_root) if d.is_relative_to(project_root) else d
            f.write(f"  - `{rel}`\n")
        f.write("\n> **Safety guarantee:** no files were deleted, moved, or renamed.\n\n")
        f.write("---\n\n")

        # Summary table
        wasted = sum(g["size_bytes"] * (g["count"] - 1) for g in exact_groups)
        f.write("## Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Exact duplicate groups | {len(exact_groups)} |\n")
        f.write(f"| Files in duplicate groups | {sum(g['count'] for g in exact_groups)} |\n")
        f.write(f"| Cross-tree duplicate groups (archive ↔ thesis) | {len(cross_groups)} |\n")
        f.write(f"| Name-collision groups (same name, diff hash) | {len(name_collisions)} |\n")
        f.write(f"| Reclaimable space (duplicates only) | {_fmt_size(wasted)} |\n")
        f.write("\n---\n\n")

        # Section 1 – exact duplicates
        f.write("## Section 1 — Exact Duplicates (same hash)\n\n")
        if not exact_groups:
            f.write("_No exact duplicates found._\n\n")
        else:
            f.write(
                "Files with identical SHA-256 hashes. "
                "Marked `[CROSS-TREE]` when copies exist in both `archive/` and `thesis/`.\n\n"
            )
            for i, g in enumerate(exact_groups, 1):
                tag = " `[CROSS-TREE]`" if g["hash"] in cross_hashes else ""
                f.write(f"### {i}. {', '.join(g['filenames'])}{tag}\n\n")
                f.write(f"| Field | Value |\n")
                f.write(f"|-------|-------|\n")
                f.write(f"| Hash (SHA-256) | `{g['hash']}` |\n")
                f.write(f"| File size | {_fmt_size(g['size_bytes'])} |\n")
                f.write(f"| Duplicate count | {g['count']} |\n")
                f.write(f"| Recommendation | {recommendation(g, g['hash'] in cross_hashes)} |\n\n")
                f.write("**All paths:**\n\n")
                for p in g["paths"]:
                    rel = Path(p).relative_to(project_root) if Path(p).is_relative_to(project_root) else Path(p)
                    f.write(f"- `{rel}`\n")
                f.write("\n")

        f.write("---\n\n")

        # Section 2 – cross-tree duplicates
        f.write("## Section 2 — Cross-Tree Duplicates (archive/ ↔ thesis/)\n\n")
        if not cross_groups:
            f.write("_No cross-tree duplicates found._\n\n")
        else:
            f.write(
                f"These {len(cross_groups)} file(s) appear in **both** `archive/` and "
                "`thesis/refs/papers_all/` with identical content.\n\n"
            )
            for i, g in enumerate(cross_groups, 1):
                f.write(f"### {i}. {', '.join(g['filenames'])}\n\n")
                f.write(f"| Field | Value |\n")
                f.write(f"|-------|-------|\n")
                f.write(f"| Hash (SHA-256) | `{g['hash']}` |\n")
                f.write(f"| File size | {_fmt_size(g['size_bytes'])} |\n")
                archive_ps = [p for p in g["paths"] if "archive" + os.sep in p or "archive/" in p]
                thesis_ps = [p for p in g["paths"] if "thesis" + os.sep in p or "thesis/" in p]
                f.write(f"| archive/ copies | {len(archive_ps)} |\n")
                f.write(f"| thesis/ copies | {len(thesis_ps)} |\n\n")
                f.write("**archive/ paths:**\n\n")
                for p in archive_ps:
                    rel = Path(p).relative_to(project_root) if Path(p).is_relative_to(project_root) else Path(p)
                    f.write(f"- `{rel}`\n")
                f.write("\n**thesis/ paths:**\n\n")
                for p in thesis_ps:
                    rel = Path(p).relative_to(project_root) if Path(p).is_relative_to(project_root) else Path(p)
                    f.write(f"- `{rel}`\n")
                f.write("\n")

        f.write("---\n\n")

        # Section 3 – name collisions
        f.write("## Section 3 — Name Collisions (same filename, different hash)\n\n")
        if not name_collisions:
            f.write("_No name collisions found._\n\n")
        else:
            f.write(
                f"These {len(name_collisions)} filename(s) appear more than once with **different content**. "
                "This may indicate different versions of the same paper.\n\n"
            )
            for i, c in enumerate(name_collisions, 1):
                f.write(f"### {i}. `{c['filename']}`\n\n")
                for j, v in enumerate(c["variants"], 1):
                    f.write(f"**Variant {j}** — hash `{v['hash']}`, size {_fmt_size(v['size_bytes'])}\n\n")
                    for p in v["paths"]:
                        rel = Path(p).relative_to(project_root) if Path(p).is_relative_to(project_root) else Path(p)
                        f.write(f"- `{rel}`\n")
                    f.write("\n")

        f.write("---\n\n")
        f.write("_Report generated by `scripts/find_duplicate_papers.py` — read-only scan, no files modified._\n")


def write_csv(
    output_path: Path,
    exact_groups: list[dict],
    cross_hashes: set[str],
    project_root: Path,
) -> None:
    rows = []
    for g in exact_groups:
        is_cross = g["hash"] in cross_hashes
        for p in g["paths"]:
            rel = Path(p).relative_to(project_root) if Path(p).is_relative_to(project_root) else Path(p)
            rows.append(
                {
                    "hash_sha256": g["hash"],
                    "filename": Path(p).name,
                    "relative_path": str(rel).replace("\\", "/"),
                    "size_bytes": g["size_bytes"],
                    "size_human": _fmt_size(g["size_bytes"]),
                    "duplicate_count": g["count"],
                    "is_cross_tree": "YES" if is_cross else "NO",
                    "recommendation": recommendation(g, is_cross),
                }
            )
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "hash_sha256",
                "filename",
                "relative_path",
                "size_bytes",
                "size_human",
                "duplicate_count",
                "is_cross_tree",
                "recommendation",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Detect duplicate PDF papers (read-only).")
    parser.add_argument(
        "--root",
        default=None,
        help="Project root directory (default: parent of this script's directory).",
    )
    args = parser.parse_args()

    project_root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    scan_dirs = [project_root / d for d in SCAN_DIRS_REL]
    output_dir = project_root / OUTPUT_DIR_REL
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n  Duplicate Paper Finder")
    print(f"  Project root : {project_root}")
    print(f"  Timestamp    : {ts}")
    print()

    # 1. Collect PDFs
    print("  Step 1/4  Collecting PDF files …")
    pdfs = collect_pdfs(scan_dirs)
    print(f"            Found {len(pdfs)} PDF files.")

    # 2. Build hash + name index
    print("  Step 2/4  Hashing files …")
    hash_map, name_map = build_index(pdfs)

    # 3. Analyse
    print("  Step 3/4  Analysing …")
    exact_groups = exact_duplicate_groups(hash_map)
    cross_groups = cross_tree_groups(exact_groups, project_root)
    name_collisions = name_collision_groups(name_map)
    cross_hashes = {g["hash"] for g in cross_groups}

    print(f"            Exact duplicate groups  : {len(exact_groups)}")
    print(f"            Cross-tree groups        : {len(cross_groups)}")
    print(f"            Name collision groups    : {len(name_collisions)}")

    # 4. Write outputs
    print("  Step 4/4  Writing reports …")
    md_path = output_dir / REPORT_MD
    csv_path = output_dir / REPORT_CSV

    write_markdown(md_path, exact_groups, cross_groups, name_collisions, len(pdfs), scan_dirs, project_root, ts)
    write_csv(csv_path, exact_groups, cross_hashes, project_root)

    print(f"\n  Reports written:")
    print(f"    {md_path.relative_to(project_root)}")
    print(f"    {csv_path.relative_to(project_root)}")
    print(f"\n  SAFETY: No files were deleted, moved, or renamed.\n")


if __name__ == "__main__":
    main()
