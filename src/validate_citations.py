"""
validate_citations.py -- Check that ledger citations resolve in the source PDF.
===============================================================================

For each row in data/ledger/bhp_sources.csv, checks that:
  (a) the cited value appears on the cited page, and
  (b) the section/note name appears on the same page.

Flags mismatches. Does NOT prove the number is correct -- it proves that
something matching the number appears on the page you cited. That is enough
to catch "right document, wrong page" and "I changed the value but forgot to
update the citation" errors.

Requires pdfplumber (pip install pdfplumber) and a local copy of the AR25 PDF
(not committed -- it is copyrighted; download from bhp.com/investors/results).

Usage
-----
    python src/validate_citations.py \\
        --ledger data/ledger/bhp_sources.csv \\
        --pdf    data/raw/250819_bhpresults_fy25.pdf

    python src/validate_citations.py \\
        --ledger data/ledger/bhp_sources.csv \\
        --pdf    data/raw/250819_bhpresults_fy25.pdf \\
        --strict        # exit 1 if any mismatch found

Output
------
A table showing FOUND / NOT FOUND for each fact, with the cited page and section.
Rows where both value and section are found on the page are the happy path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def _page_text(pdf, page_num: int) -> str:
    """Return extracted text for a 1-indexed page (handles pdfplumber 0-indexing)."""
    idx = page_num - 1
    if idx < 0 or idx >= len(pdf.pages):
        return ""
    return pdf.pages[idx].extract_text() or ""


def _value_in_text(value: str, text: str) -> bool:
    """Check whether the numeric value (or a reasonable rendering) appears in the text."""
    # Try exact, then with comma-thousands separators
    clean = str(value).strip()
    if not clean or clean.lower() in ("", "n/a", "live"):
        return True  # live/derived values can't be checked statically
    # Try the raw value and a comma-formatted version
    candidates = [clean]
    try:
        num = float(clean.replace(",", ""))
        if num >= 1000:
            candidates.append(f"{num:,.0f}")
        if num >= 10:
            candidates.append(f"{num:.0f}")
    except ValueError:
        pass
    return any(c in text for c in candidates)


def validate_citations(ledger_path: str, pdf_path: str, strict: bool = False) -> pd.DataFrame:
    try:
        import pdfplumber
    except ImportError:
        sys.exit("pdfplumber is not installed. Run: pip install pdfplumber")

    ledger = pd.read_csv(ledger_path)

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        sys.exit(
            f"PDF not found at {pdf_path}.\n"
            "Download the BHP results PDF from bhp.com/investors and place it in data/raw/.\n"
            "It is not committed (copyrighted); the ledger CSV is committed instead."
        )

    results = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for _, row in ledger.iterrows():
            raw_page = str(row.get("Page", "")).strip()
            if not raw_page or raw_page.lower() in ("n/a", ""):
                results.append({
                    "Fact": row["Fact"],
                    "Value": row["Value"],
                    "Page": raw_page,
                    "Value found": "SKIP (no page)",
                    "Section found": "SKIP",
                })
                continue

            # Page may be a range like "140 + 142" -- check first page cited
            first_page_str = raw_page.split("+")[0].strip().split("-")[0].strip()
            try:
                page_num = int(first_page_str)
            except ValueError:
                results.append({
                    "Fact": row["Fact"],
                    "Value": row["Value"],
                    "Page": raw_page,
                    "Value found": f"SKIP (unparseable page: {raw_page})",
                    "Section found": "SKIP",
                })
                continue

            if page_num > total_pages:
                results.append({
                    "Fact": row["Fact"],
                    "Value": row["Value"],
                    "Page": raw_page,
                    "Value found": f"SKIP (PDF has {total_pages} pages; cited {page_num})",
                    "Section found": "SKIP",
                })
                continue

            text = _page_text(pdf, page_num)

            val_found = _value_in_text(str(row["Value"]), text)
            section = str(row.get("Section / Note", "") or "")
            # Only check the first keyword of the section name (enough to fingerprint)
            section_keyword = section.split("—")[0].strip().split("-")[0].strip()
            sec_found = (not section_keyword) or any(
                kw.lower() in text.lower()
                for kw in [section_keyword, section_keyword.replace("Note ", "")]
                if kw.strip()
            )

            results.append({
                "Fact": row["Fact"][:60],
                "Value": row["Value"],
                "Page": page_num,
                "Value found": "OK" if val_found else "NOT FOUND",
                "Section found": "OK" if sec_found else "CHECK",
            })

    df = pd.DataFrame(results)

    # Print
    pd.set_option("display.max_colwidth", 62)
    pd.set_option("display.width", 120)
    print(df.to_string(index=False))

    mismatches = df[df["Value found"] == "NOT FOUND"]
    print(f"\n{len(df)} entries checked | {len(mismatches)} value mismatches")

    if strict and not mismatches.empty:
        print("\nFailing rows:")
        print(mismatches.to_string(index=False))
        sys.exit(f"Citation validation failed: {len(mismatches)} mismatches found.")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate ledger citations against the source PDF."
    )
    parser.add_argument("--ledger", default="data/ledger/bhp_sources.csv",
                        help="Path to the citation ledger CSV")
    parser.add_argument("--pdf", required=True,
                        help="Path to the local source PDF (not committed)")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 if any value is not found on its cited page")
    args = parser.parse_args()
    validate_citations(args.ledger, args.pdf, strict=args.strict)


if __name__ == "__main__":
    main()
