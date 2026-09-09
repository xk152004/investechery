#!/usr/bin/env python3
"""Walk a folder and emit a Markdown link for every HTML / PDF file.

Usage:
    python3 make_links.py [FOLDER] [-o OUTPUT.md] [--prefix URL_PREFIX] [--all]

Each line of the output looks like:
    - [Meta Platforms Business Overview](https://xk152004.github.io/investechery/archive/Meta-Platforms-Business-Overview.html)
"""

import argparse
import os
import re
import sys
from urllib.parse import quote

DEFAULT_PREFIX = "https://xk152004.github.io/investechery/stocks/"
EXTENSIONS = {".html", ".htm", ".pdf"}

# Words that should stay lowercase in the middle of a title.
SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on",
    "or", "the", "to", "vs", "with",
}

# Tokens that should keep a fixed spelling.
SPECIAL = {
    "pdf": "PDF", "html": "HTML", "us": "US", "uk": "UK", "eu": "EU",
    "ai": "AI", "ipo": "IPO", "ceo": "CEO", "cfo": "CFO", "esg": "ESG",
    "roic": "ROIC", "dcf": "DCF", "tam": "TAM", "capex": "capex",
    "yoy": "YoY", "fy": "FY", "q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4",
}


def titleize(stem: str) -> str:
    """Turn a file name stem into a human-readable title."""
    # Separators -> spaces, but keep em/en dashes as visible separators.
    text = re.sub(r"[_\-]+", " ", stem)
    text = re.sub(r"\s+", " ", text).strip()
    # Split camelCase only when it is unambiguous (aB -> a B).
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)

    words = text.split(" ")
    out = []
    for i, w in enumerate(words):
        if not w:
            continue
        low = w.lower()
        if low in SPECIAL:
            out.append(SPECIAL[low])
        elif w.isupper():           # already an acronym: AXT, GOOG, META
            out.append(w)
        elif any(c.isupper() for c in w[1:]):   # mixed case: keep as authored
            out.append(w)
        elif low in SMALL_WORDS and 0 < i < len(words) - 1:
            out.append(low)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out) if out else stem


def url_for(rel_path: str, prefix: str) -> str:
    parts = rel_path.split(os.sep)
    return prefix.rstrip("/") + "/" + "/".join(quote(p) for p in parts)


def collect(root: str, prefix: str, include_hidden: bool):
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        dirnames.sort()
        for name in sorted(filenames):
            if not include_hidden and name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in EXTENSIONS:
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            title = titleize(os.path.splitext(name)[0])
            if ext == ".pdf":
                title += " (PDF)"
            rows.append((rel, title, url_for(rel, prefix)))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", default=".", help="folder to walk (default: .)")
    ap.add_argument("-o", "--output", default="links.md", help="output Markdown file (default: links.md)")
    ap.add_argument("--prefix", default=DEFAULT_PREFIX, help="URL prefix (default: %(default)s)")
    ap.add_argument("--all", action="store_true", help="include hidden files and folders")
    args = ap.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(args.folder))
    if not os.path.isdir(root):
        sys.exit(f"error: not a folder: {root}")

    rows = collect(root, args.prefix, args.all)
    with open(args.output, "w", encoding="utf-8") as fh:
        for _rel, title, url in rows:
            fh.write(f"- [{title}]({url})\n")

    print(f"{len(rows)} link(s) written to {os.path.abspath(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
