#!/usr/bin/env python3
"""
scripts/extract_papers_to_text.py
==================================
Converts every PDF under Thesis_report/ to a plain-text file at
Thesis_report/papers_text/<same_name>.txt

Usage:
    python scripts/extract_papers_to_text.py
    python scripts/extract_papers_to_text.py --root Thesis_report/
    python scripts/extract_papers_to_text.py --root Thesis_report/ --max-pages 30

Requires:
    pip install pymupdf          # PyMuPDF (fitz) — fastest, best layout
    OR pip install pdfminer.six  # fallback if PyMuPDF unavailable
"""

import argparse
import json
import sys
from pathlib import Path


def _extract_with_fitz(pdf_path: Path, max_pages: int) -> str:
    """Extract text using PyMuPDF (fitz)."""
    import fitz  # type: ignore

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        if max_pages and i >= max_pages:
            pages.append(f"\n[... truncated at page {max_pages} of {len(doc)} ...]\n")
            break
        text = page.get_text("text")
        pages.append(f"--- PAGE {i + 1} ---\n{text}")
    doc.close()
    return "\n".join(pages)


def _extract_with_pdfminer(pdf_path: Path, max_pages: int) -> str:
    """Fallback extraction using pdfminer.six."""
    from io import StringIO

    from pdfminer.high_level import extract_text_to_fp  # type: ignore
    from pdfminer.layout import LAParams  # type: ignore

    buf = StringIO()
    with open(pdf_path, "rb") as fh:
        extract_text_to_fp(
            fh,
            buf,
            laparams=LAParams(),
            maxpages=max_pages or 0,
            output_type="text",
            codec="utf-8",
        )
    return buf.getvalue()


def extract_one(pdf_path: Path, max_pages: int = 0) -> str:
    """Try PyMuPDF, fall back to pdfminer.six, raise if neither available."""
    try:
        return _extract_with_fitz(pdf_path, max_pages)
    except ImportError:
        pass

    try:
        return _extract_with_pdfminer(pdf_path, max_pages)
    except ImportError:
        pass

    raise RuntimeError(
        "No PDF library found. Install one of:\n"
        "  pip install pymupdf\n"
        "  pip install pdfminer.six"
    )


def main():
    parser = argparse.ArgumentParser(description="Convert Thesis_report PDFs to .txt files")
    parser.add_argument(
        "--root",
        default="Thesis_report",
        help="Root directory to search recursively for PDFs (default: Thesis_report/)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory for .txt files (default: <root>/papers_text/)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Maximum pages to extract per PDF (0 = all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract even if .txt already exists",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: Root directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else root / "papers_text"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Discover PDFs recursively
    pdfs = sorted(root.rglob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found under {root}")
        sys.exit(0)

    print(f"Found {len(pdfs)} PDF(s) under {root}")
    manifest = []

    for pdf in pdfs:
        out_name = pdf.stem + ".txt"
        out_path = out_dir / out_name

        if out_path.exists() and not args.force:
            print(f"  SKIP (exists): {pdf.name} -> {out_path.name}")
            manifest.append(
                {"pdf": str(pdf), "txt": str(out_path), "status": "skipped"}
            )
            continue

        print(f"  Extracting: {pdf.name} ...", end=" ", flush=True)
        try:
            text = extract_one(pdf, max_pages=args.max_pages)
            out_path.write_text(text, encoding="utf-8")
            n_chars = len(text)
            print(f"OK ({n_chars:,} chars -> {out_path.name})")
            manifest.append(
                {
                    "pdf": str(pdf),
                    "txt": str(out_path),
                    "status": "ok",
                    "n_chars": n_chars,
                }
            )
        except Exception as exc:
            print(f"FAILED: {exc}")
            manifest.append(
                {"pdf": str(pdf), "txt": str(out_path), "status": "failed", "error": str(exc)}
            )

    # Write manifest
    manifest_path = out_dir / "extraction_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written: {manifest_path}")

    ok = sum(1 for m in manifest if m["status"] == "ok")
    fail = sum(1 for m in manifest if m["status"] == "failed")
    skip = sum(1 for m in manifest if m["status"] == "skipped")
    print(f"Summary: {ok} extracted, {skip} skipped, {fail} failed")

    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()

