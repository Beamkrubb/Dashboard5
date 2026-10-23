"""
Dump every table in a PDF to CSV so province tables (D01 rice history, D04 irrigated
area) can be picked out and saved under data/raw/<ID>/.

    python scripts/extract_pdf_tables.py data/raw/D04/rid_annual_2566.pdf --pages 10-25

Output: <pdf_stem>_tables/page<NNN>_t<k>.csv  (UTF-8 with BOM, opens in Excel)
Requires: pip install pdfplumber
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_pages(spec: str | None, n: int):
    if not spec:
        return range(n)
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out.extend(range(int(a) - 1, int(b or a)))
    return [p for p in out if 0 <= p < n]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="e.g. 3-7,12")
    args = ap.parse_args(argv)
    import pdfplumber

    pdf_path = Path(args.pdf)
    out_dir = pdf_path.with_name(pdf_path.stem + "_tables")
    out_dir.mkdir(exist_ok=True)
    count = 0
    with pdfplumber.open(pdf_path) as pdf:
        for i in parse_pages(args.pages, len(pdf.pages)):
            for k, table in enumerate(pdf.pages[i].extract_tables(), 1):
                dest = out_dir / f"page{i + 1:03d}_t{k}.csv"
                with dest.open("w", newline="", encoding="utf-8-sig") as fh:
                    csv.writer(fh).writerows(table)
                count += 1
    print(f"{count} tables -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
