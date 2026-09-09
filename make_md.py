#!/usr/bin/env python3
"""Create one Markdown file per name in the current folder.

Usage:
    python3 make_md.py Alphabet Meta "SK hynix"
    python3 make_md.py "Alphabet Meta NVDA"      # one quoted, space-separated list
"""

import os
import re
import sys


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s.-]", "", name).strip()
    return re.sub(r"\s+", "-", s) or "untitled"


def main(argv):
    # One quoted argument -> split it on spaces. Several arguments -> each is a
    # name, so multi-word names survive quoting.
    names = argv[0].split() if len(argv) == 1 else [a.strip() for a in argv]
    names = [n for n in names if n]
    if not names:
        sys.exit("usage: python3 make_md.py NAME [NAME ...]")

    for name in names:
        path = os.path.join(os.getcwd(), slug(name) + ".md")
        if os.path.exists(path):
            print(f"skipped (exists): {path}")
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"\n")
        print(f"created: {path}")


if __name__ == "__main__":
    main(sys.argv[1:])
