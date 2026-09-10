#!/usr/bin/env python3
"""
Save Arm Holdings (ARM) earnings call transcripts into sources/Transcripts/ -- no prompts.

  1. Fetches every ARM earnings-call transcript from the last 10 years on
     stockanalysis.com (text sourced from Quartr) and writes each one as Markdown.
  2. Moves any ARM transcript files already in ~/Downloads into the same folder.

Existing files are skipped, so it is safe to re-run after each earnings call.
Uses only the Python standard library plus the system `curl`.

Usage (from Terminal):   python3 fetch_arm_transcripts.py
  --years N      look-back window in years (default 10)
  --no-fetch     only sweep ~/Downloads
  --force        overwrite existing transcript files
"""
import argparse, datetime as dt, html, re, shutil, subprocess, sys, time
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://stockanalysis.com"
INDEX = BASE + "/stocks/arm/transcripts/"
ROOT = Path(__file__).resolve().parent            # ARM_ARM_HOLDINGS_PLC_UK/
OUT = ROOT / "sources" / "Transcripts"
DOWNLOADS = Path.home() / "Downloads"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
# Known post-IPO calls, used if the index page cannot be parsed.
FALLBACK = ["114410-q2-2024", "130028-q3-2024", "181996-q4-2024", "165500-q1-2025",
            "217577-q2-2025", "253579-q3-2025", "303195-q4-2025", "343702-q1-2026",
            "368952-q2-2026", "411181-q3-2026", "530403-q4-2026", "632326-q1-2027"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}


def get(url):
    r = subprocess.run(["curl", "-sSL", "--fail", "--max-time", "60", "-A", UA, url],
                       capture_output=True)
    if r.returncode:
        raise RuntimeError(f"curl failed ({r.returncode}) for {url}: {r.stderr.decode()[:200]}")
    return r.stdout.decode("utf-8", "replace")


# ---- minimal DOM ----------------------------------------------------------
class Node:
    __slots__ = ("tag", "attrs", "kids", "parent")
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent = tag, dict(attrs), [], parent
    def cls(self):
        return (self.attrs.get("class") or "").split()
    def text(self):
        return "".join(k if isinstance(k, str) else k.text() for k in self.kids)
    def elems(self):
        return [k for k in self.kids if isinstance(k, Node)]
    def walk(self):
        for k in self.elems():
            yield k
            yield from k.walk()


class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None); self.cur = self.root
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur); self.cur.kids.append(n)
        if tag == "br": n.kids.append(" ")
        if tag not in VOID: self.cur = n
    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))
    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag: n = n.parent
        if n is not None and n.parent is not None: self.cur = n.parent
    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(page):
    p = DOM(); p.feed(page); return p.root


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


# ---- transcript extraction ------------------------------------------------
def extract(page):
    root = parse(page)
    h1 = next((n for n in root.walk() if n.tag == "h1"), None)
    title = clean(h1.text()) if h1 else ""
    m = re.search(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", clean(h1.parent.text()) if h1 else "")
    date = dt.datetime.strptime(m.group(0), "%b %d, %Y").date() if m else None
    art = next((n for n in root.walk() if n.attrs.get("aria-label") == "Full transcript"), None)
    if art is None:
        raise ValueError("full-transcript block not found (layout changed or paywalled?)")
    blocks = []
    for b in art.walk():
        if b.tag != "div" or "border-t" not in b.cls():
            continue
        name_el = next((k for k in b.walk() if "font-bold" in k.cls()), None)
        name = clean(name_el.text()) if name_el else ""
        role = " ".join(clean(k.text()) for k in b.elems()
                        if k.tag != "p" and k is not name_el and clean(k.text()))
        paras = [clean(k.text()) for k in b.walk() if k.tag == "p"]
        paras = [p for p in paras if p]
        if name or paras:
            blocks.append((name, role, paras))
    if not blocks:
        raise ValueError("no speaker blocks found")
    return title, date, blocks


def to_markdown(q, fy, date, url, blocks):
    seen = {}
    for n, r, _ in blocks:
        if n and n != "Operator" and n not in seen: seen[n] = r
    lines = [f"# Arm Holdings plc (ARM) — Q{q} FY{fy} Earnings Call Transcript", "",
             f"- Call date: {date.isoformat()}", f"- Source: {url}",
             "- Transcript provider (per source page): Quartr, via stockanalysis.com",
             f"- Retrieved: {dt.date.today().isoformat()}", "", "## Participants", ""]
    lines += [f"- {n}" + (f" — {r}" if r else "") for n, r in seen.items()]
    lines += ["", "## Transcript", ""]
    for n, r, paras in blocks:
        lines += [f"**{n}**" + (f" ({r})" if r else ""), ""]
        for p in paras: lines += [p, ""]
    return "\n".join(lines)


def discover():
    try:
        slugs = sorted(set(re.findall(r"/stocks/arm/transcripts/(\d+-q\d-\d{4})/", get(INDEX))))
        return slugs or FALLBACK
    except Exception as e:
        print(f"! index fetch failed ({e}); using built-in list")
        return FALLBACK


def fetch_all(years, force):
    OUT.mkdir(parents=True, exist_ok=True)
    cutoff = dt.date.today() - dt.timedelta(days=round(365.25 * years))
    saved = skipped = 0
    for slug in discover():
        q, fy = re.search(r"q(\d)-(\d{4})", slug).groups()
        if int(fy) < cutoff.year - 1:            # clearly older than the window
            continue
        existing = list(OUT.glob(f"*_Q{q}_FY{fy}_Earnings_Call_Transcript.md"))
        if existing and not force:
            print(f"= exists  {existing[0].name}"); skipped += 1; continue
        url = f"{INDEX}{slug}/"
        try:
            title, date, blocks = extract(get(url))
        except Exception as e:
            print(f"! failed  {slug}: {e}"); continue
        if date is None or date < cutoff:
            continue                              # outside the look-back window
        name = f"{date.isoformat()}_Q{q}_FY{fy}_Earnings_Call_Transcript.md"
        md = to_markdown(q, fy, date, url, blocks)
        (OUT / name).write_text(md, encoding="utf-8")
        words = sum(len(" ".join(p).split()) for _, _, p in blocks)
        print(f"+ saved   {name}  ({len(blocks)} speaker turns, {words:,} words)")
        saved += 1
        time.sleep(1)                             # be polite to the site
    return saved, skipped


def sweep_downloads():
    moved = 0
    if not DOWNLOADS.is_dir():
        return moved
    pats = ["*_Earnings_Call_Transcript.md", "*ARM*ranscript*", "*Arm*ranscript*", "*arm*ranscript*"]
    for pat in pats:
        for f in DOWNLOADS.glob(pat):
            if not f.is_file(): continue
            dest = OUT / f.name
            if dest.exists():
                print(f"= in Downloads but already saved: {f.name}"); continue
            OUT.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), dest); moved += 1
            print(f"> moved   {f.name}  (from Downloads)")
    return moved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=float, default=10)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    print(f"Target folder: {OUT}")
    saved = skipped = 0
    if not a.no_fetch:
        saved, skipped = fetch_all(a.years, a.force)
    moved = sweep_downloads()
    print(f"\nDone: {saved} fetched, {moved} moved from Downloads, {skipped} already present.")
    print(f"{len(list(OUT.glob('*.md')))} transcript file(s) now in {OUT}")


if __name__ == "__main__":
    sys.exit(main())
