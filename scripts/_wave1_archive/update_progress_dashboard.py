#!/usr/bin/env python3
"""
Thesis Progress Dashboard Generator
====================================

Reads a YAML progress config and generates a Markdown dashboard
with TRS (Thesis Readiness Score) and ERS (Engineering Readiness Score).

Usage:
    python scripts/update_progress_dashboard.py --config progress.yaml --output DASHBOARD.md
"""

import argparse
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

REQUIRED_KEYS = {"snapshot_date", "deadline", "sections", "month_milestones"}

# TRS weights
W_WRITING = 0.45
W_EXPERIMENTS = 0.35
W_SYSTEM = 0.20


# ---------------------------------------------------------------------------
# Core computations
# ---------------------------------------------------------------------------

def compute_trs(writing_pct: float, experiments_pct: float, system_pct: float) -> float:
    """
    Thesis Readiness Score = 0.45*writing + 0.35*experiments + 0.20*system.
    """
    return round(W_WRITING * writing_pct + W_EXPERIMENTS * experiments_pct + W_SYSTEM * system_pct, 1)


def compute_ers(system_pct: float) -> float:
    """Engineering Readiness Score (mirrors system completeness)."""
    return system_pct


def weeks_remaining(snapshot_date: str, deadline: str) -> int:
    """Return whole weeks between *snapshot_date* and *deadline* (≥ 0)."""
    snap = datetime.strptime(snapshot_date, "%Y-%m-%d")
    dead = datetime.strptime(deadline, "%Y-%m-%d")
    delta = (dead - snap).days
    return max(0, delta // 7)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ascii_bar(percent: float, width: int = 20) -> str:
    """
    Return a fixed-*width* bar using Unicode block chars.

    █ = filled, ░ = empty.  *percent* is clamped to [0, 100].
    """
    percent = max(0.0, min(100.0, percent))
    filled = round(width * percent / 100)
    return "\u2588" * filled + "\u2591" * (width - filled)


def checklist_summary(items: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Return (done_count, total_count) for a list of checklist items."""
    if not items:
        return 0, 0
    done = sum(1 for item in items if item.get("done", False))
    return done, len(items)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(path: Path) -> Dict[str, Any]:
    """
    Load and validate a progress YAML file.

    Raises ``ValueError`` if required top-level keys are missing.
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"Config missing required keys: {missing}")

    return data


# ---------------------------------------------------------------------------
# Dashboard generation
# ---------------------------------------------------------------------------

def generate_dashboard(data: Dict[str, Any]) -> str:
    """
    Render the full Markdown dashboard string from parsed YAML *data*.
    """
    sections = data["sections"]
    milestones = data["month_milestones"]
    snapshot = data["snapshot_date"]
    deadline = data["deadline"]

    writing_pct = sections.get("writing", {}).get("percent", 0)
    experiments_pct = sections.get("experiments", {}).get("percent", 0)
    system_pct = sections.get("system", {}).get("percent", 0)

    trs = compute_trs(writing_pct, experiments_pct, system_pct)
    ers = compute_ers(system_pct)
    weeks = weeks_remaining(snapshot, deadline)

    lines: List[str] = []
    lines.append("# Thesis Progress Dashboard")
    lines.append("")
    lines.append(f"**Snapshot:** {snapshot}  ")
    lines.append(f"**Deadline:** {deadline} ({weeks} weeks remaining)")
    lines.append("")

    # Headline scores
    lines.append("## Headline Scores")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Thesis Readiness Score (TRS) | {trs}% |")
    lines.append(f"| Engineering Readiness Score (ERS) | {ers}% |")
    lines.append("")

    # Section progress
    lines.append("## Section Progress")
    lines.append("")
    lines.append("| Section | Progress | Bar |")
    lines.append("|---|---|---|")
    for name, info in sections.items():
        pct = info.get("percent", 0)
        bar = ascii_bar(pct, width=20)
        lines.append(f"| {name} | {pct}% | {bar} |")
    lines.append("")

    # Checklists
    lines.append("## Checklists")
    lines.append("")
    for name, info in sections.items():
        items = info.get("checklist", [])
        done, total = checklist_summary(items)
        lines.append(f"### {name} ({done}/{total})")
        lines.append("")
        for item in items:
            mark = "x" if item.get("done") else " "
            lines.append(f"- [{mark}] {item['item']}")
        lines.append("")

    # Month milestones table
    lines.append("## Month Milestones")
    lines.append("")
    lines.append("| Month | Label | Period | Status | % |")
    lines.append("|---|---|---|---|---|")
    for ms in milestones:
        lines.append(
            f"| {ms['month']} | {ms['label']} | {ms['period']} "
            f"| {ms['status']} | {ms['percent']}% |"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate thesis progress dashboard")
    parser.add_argument("--config", type=Path, required=True, help="Path to progress YAML")
    parser.add_argument("--output", type=Path, default=None, help="Output markdown file")
    args = parser.parse_args()

    data = load_config(args.config)
    md = generate_dashboard(data)

    if args.output:
        args.output.write_text(md, encoding="utf-8")
        print(f"Dashboard written to {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
