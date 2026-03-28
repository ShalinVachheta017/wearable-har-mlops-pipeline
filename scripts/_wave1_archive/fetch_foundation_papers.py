"""
scripts/fetch_foundation_papers.py
===================================
Downloads 5 foundational primary-source PDFs into Thesis_report/refs/.
Falls back gracefully to printing manual URLs if network is unavailable.

Usage:
    python scripts/fetch_foundation_papers.py
    python scripts/fetch_foundation_papers.py --dry-run   # print URLs only

Each PDF is verified to be > 200 KB after download.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

REFS_DIR = Path(__file__).parent.parent / "Thesis_report" / "refs"

# (stable_filename, primary_url, fallback_url, description)
PAPERS: list[tuple[str, str, str, str]] = [
    (
        "adabn_li2016_1603.04779.pdf",
        "https://arxiv.org/pdf/1603.04779",
        "https://arxiv.org/pdf/1603.04779v2",
        "Li et al. (2016) Revisiting Batch Normalization For Practical Domain Adaptation",
    ),
    (
        "tent_wang2021_openreview_uXl3bZLkr3c.pdf",
        "https://arxiv.org/pdf/2006.10726",
        "https://arxiv.org/pdf/2006.10726v3",
        "Wang et al. (2021) Tent: Fully Test-Time Adaptation by Entropy Minimization",
    ),
    (
        "ewc_kirkpatrick2017_1612.00796.pdf",
        "https://arxiv.org/pdf/1612.00796",
        "https://arxiv.org/pdf/1612.00796v2",
        "Kirkpatrick et al. (2017) Overcoming catastrophic forgetting in neural networks",
    ),
    (
        "calibration_guo2017_1706.04599.pdf",
        "https://arxiv.org/pdf/1706.04599",
        "https://arxiv.org/pdf/1706.04599v2",
        "Guo et al. (2017) On Calibration of Modern Neural Networks",
    ),
    (
        "mc_dropout_gal2016_1506.02142.pdf",
        "https://arxiv.org/pdf/1506.02142",
        "https://arxiv.org/pdf/1506.02142v6",
        "Gal & Ghahramani (2016) Dropout as a Bayesian Approximation",
    ),
]

MIN_SIZE_BYTES = 200_000  # 200 KB minimum to confirm it's a real PDF


def _try_download(url: str, dest: Path, description: str, attempt: int = 1) -> bool:
    """Return True on success."""
    print(f"  [attempt {attempt}] GET {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; thesis-mlops-fetch/1.0; "
                    "+https://github.com/ShalinVachheta017/MasterArbeit_MLops)"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if len(data) < MIN_SIZE_BYTES:
            print(f"  WARNING: file too small ({len(data)} bytes) — likely a redirect page, not a PDF")
            return False
        dest.write_bytes(data)
        print(f"  OK  {dest.name}  ({len(data) / 1024:.0f} KB)")
        return True
    except Exception as exc:
        print(f"  FAIL {exc}")
        return False


def _manual_url_hint(fname: str, primary: str, description: str) -> None:
    print(f"\n  Manual download required for:  {description}")
    print(f"  URL   : {primary}")
    print(f"  Save to: {REFS_DIR / fname}")


def main(dry_run: bool = False) -> int:
    REFS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target directory: {REFS_DIR.resolve()}\n")

    results: dict[str, str] = {}  # fname -> status

    for fname, primary, fallback, description in PAPERS:
        dest = REFS_DIR / fname
        print(f"--- {description}")

        if dest.exists() and dest.stat().st_size >= MIN_SIZE_BYTES:
            print(f"  SKIP already exists ({dest.stat().st_size / 1024:.0f} KB)")
            results[fname] = "SKIPPED (already present)"
            continue

        if dry_run:
            _manual_url_hint(fname, primary, description)
            results[fname] = "DRY_RUN"
            continue

        # Try primary URL first, then fallback
        ok = _try_download(primary, dest, description, attempt=1)
        if not ok:
            time.sleep(2)
            ok = _try_download(fallback, dest, description, attempt=2)

        if ok:
            results[fname] = f"DOWNLOADED ({dest.stat().st_size / 1024:.0f} KB)"
        else:
            _manual_url_hint(fname, primary, description)
            results[fname] = "FAILED — manual download required"

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    failed = 0
    for fname, status in results.items():
        icon = "v" if status.startswith(("DOWNLOADED", "SKIPPED")) else "x"
        print(f"  [{icon}] {fname}  =>  {status}")
        if "FAILED" in status:
            failed += 1

    if failed:
        print(f"\n{failed} paper(s) could not be downloaded automatically.")
        print("Please download them manually using the URLs printed above.")
        print("Then re-run:  python scripts/extract_papers_to_text.py --force")
        return 1

    print("\nAll papers present. Run next:")
    print("  python scripts/extract_papers_to_text.py --force")
    print("  python scripts/regenerate_support_map.py")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download foundational PDFs to Thesis_report/refs/")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print URLs only, do not download",
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
