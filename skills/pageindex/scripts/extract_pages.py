#!/usr/bin/env python3
"""
extract_pages.py — Extract text from PDF or Markdown files for Claude-driven PageIndex generation.

No LLM API required. Uses PyMuPDF (preferred) or PyPDF2 for PDF extraction.

Usage examples:
  # Get page count + first line of each page (quick overview)
  python extract_pages.py --pdf report.pdf --overview

  # Extract specific pages as JSON
  python extract_pages.py --pdf report.pdf --start 1 --end 20

  # Extract all pages
  python extract_pages.py --pdf report.pdf

  # Read markdown file
  python extract_pages.py --md document.md

Output: JSON to stdout (pipe to file with > output.json or use --output)
"""

import sys
import json
import argparse
import os


def extract_pdf_pages(path, start=None, end=None, parser="PyMuPDF"):
    """Extract text from a range of PDF pages (1-indexed, inclusive)."""
    doc_name = os.path.basename(path)

    if parser == "PyMuPDF":
        try:
            import pymupdf
            doc = pymupdf.open(path)
            total_pages = len(doc)
            s = (start or 1) - 1          # convert to 0-indexed
            e = min(end or total_pages, total_pages)
            pages = []
            for i in range(s, e):
                text = doc[i].get_text()
                pages.append({"page": i + 1, "text": text})
            doc.close()
            return {"doc_name": doc_name, "total_pages": total_pages, "pages": pages}
        except ImportError:
            parser = "PyPDF2"   # fall back

    # PyPDF2 fallback
    import PyPDF2
    reader = PyPDF2.PdfReader(path)
    total_pages = len(reader.pages)
    s = (start or 1) - 1
    e = min(end or total_pages, total_pages)
    pages = []
    for i in range(s, e):
        text = reader.pages[i].extract_text() or ""
        pages.append({"page": i + 1, "text": text})
    return {"doc_name": doc_name, "total_pages": total_pages, "pages": pages}


def overview_pdf(path, parser="PyMuPDF"):
    """Return page count plus first ~100 chars of each page (cheap scan)."""
    doc_name = os.path.basename(path)

    if parser == "PyMuPDF":
        try:
            import pymupdf
            doc = pymupdf.open(path)
            total_pages = len(doc)
            overview = []
            for i, page in enumerate(doc):
                snippet = page.get_text()[:150].replace("\n", " ").strip()
                overview.append({"page": i + 1, "snippet": snippet})
            doc.close()
            return {"doc_name": doc_name, "total_pages": total_pages, "overview": overview}
        except ImportError:
            parser = "PyPDF2"

    import PyPDF2
    reader = PyPDF2.PdfReader(path)
    total_pages = len(reader.pages)
    overview = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        snippet = text[:150].replace("\n", " ").strip()
        overview.append({"page": i + 1, "snippet": snippet})
    return {"doc_name": doc_name, "total_pages": total_pages, "overview": overview}


def read_markdown(path):
    """Read a markdown file and return its content."""
    doc_name = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    return {"doc_name": doc_name, "total_lines": len(lines), "content": content}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract document content for PageIndex generation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", metavar="PATH", help="Path to PDF file")
    group.add_argument("--md", metavar="PATH", help="Path to Markdown file")

    parser.add_argument("--start", type=int, default=None, help="Start page (1-indexed, PDF only)")
    parser.add_argument("--end", type=int, default=None, help="End page (1-indexed inclusive, PDF only)")
    parser.add_argument("--overview", action="store_true",
                        help="PDF only: return page count + snippets, no full text")
    parser.add_argument("--parser", default="PyMuPDF", choices=["PyMuPDF", "PyPDF2"],
                        help="PDF text extractor (default: PyMuPDF)")
    parser.add_argument("--output", metavar="FILE", help="Write JSON output to file instead of stdout")

    args = parser.parse_args()

    if args.pdf:
        if not os.path.isfile(args.pdf):
            print(f"Error: file not found: {args.pdf}", file=sys.stderr)
            sys.exit(1)
        if args.overview:
            result = overview_pdf(args.pdf, parser=args.parser)
        else:
            result = extract_pdf_pages(args.pdf, start=args.start, end=args.end, parser=args.parser)
    else:
        if not os.path.isfile(args.md):
            print(f"Error: file not found: {args.md}", file=sys.stderr)
            sys.exit(1)
        result = read_markdown(args.md)

    output_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(output_str)
