#!/usr/bin/env python3
"""
Save historical earnings-call transcripts for a list of tickers -- no prompts.

Source: stockanalysis.com transcript pages (text supplied by Quartr).
Each call is written verbatim as Markdown, with speaker labels, into:

    <root>/<TICKER>_*/sources/Transcripts/     (existing research folder, if found)
    <root>/<TICKER>/sources/Transcripts/       (created otherwise)

<root> defaults to the folder this script sits in (e.g. ~/Documents/Research/Equity).
Existing files are skipped, so re-running only adds new calls.

USAGE
  python3 fetch_transcripts.py ARM NVDA MRVL          # last 10 years (default)
  python3 fetch_transcripts.py ARM --years 5
  python3 fetch_transcripts.py --file tickers.txt     # one ticker per line, # comments ok
  python3 fetch_transcripts.py                        # no tickers: use transcript_tickers.txt if
                                                      # present, else every <TICKER>_* folder under root
  python3 fetch_transcripts.py SKHY 0700.HK BRK-B    # non-US / share classes map automatically
  python3 fetch_transcripts.py XYZ=krx:000660         # or give FOLDER=exchange:code explicitly
  python3 fetch_transcripts.py META --all-events      # also investor days, keynotes, etc.
  python3 fetch_transcripts.py ARM --dry-run          # list what would be saved

OPTIONS
  --years N        look-back window in years (default 10)
  --root PATH      parent folder of the per-ticker research folders
  --all-events     include non-earnings events (investor days, M&A calls, updates)
  --force          overwrite files that already exist
  --dry-run        show what would be fetched, write nothing
  --no-downloads   don't sweep ~/Downloads for transcript files

Uses only the Python standard library plus the system `curl`.
"""
import argparse, datetime as dt, re, shutil, subprocess, sys, time
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://stockanalysis.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
DOWNLOADS = Path.home() / "Downloads"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}


# ---------------------------------------------------------------- network --
def get(url):
    r = subprocess.run(["curl", "-sSL", "--fail", "--max-time", "60", "-A", UA, url],
                       capture_output=True)
    if r.returncode:
        raise RuntimeError(f"HTTP/curl error {r.returncode} for {url}")
    return r.stdout.decode("utf-8", "replace")


# ------------------------------------------------------------ minimal DOM --
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


# ------------------------------------------------------------- extraction --
def extract(page):
    """Return (event title, call date, company name, [(speaker, role, [paragraphs])])."""
    root = parse(page)
    h1 = next((n for n in root.walk() if n.tag == "h1"), None)
    title = clean(h1.text()) if h1 else ""
    m = re.search(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", clean(h1.parent.text()) if h1 else "")
    date = dt.datetime.strptime(m.group(0), "%b %d, %Y").date() if m else None
    t = next((n for n in root.walk() if n.tag == "title"), None)
    company = re.split(r"\s*\(", clean(t.text()))[0] if t else ""
    art = next((n for n in root.walk() if n.attrs.get("aria-label") == "Full transcript"), None)
    if art is None:
        raise ValueError("full-transcript block not found (layout changed or not available)")
    blocks = []
    for b in art.walk():
        if b.tag != "div" or "border-t" not in b.cls():
            continue
        name_el = next((k for k in b.walk() if "font-bold" in k.cls()), None)
        name = clean(name_el.text()) if name_el else ""
        role = " ".join(clean(k.text()) for k in b.elems()
                        if k.tag != "p" and k is not name_el and clean(k.text()))
        paras = [p for p in (clean(k.text()) for k in b.walk() if k.tag == "p") if p]
        if name or paras:
            blocks.append((name, role, paras))
    if not blocks:
        raise ValueError("no speaker blocks found")
    return title, date, company, blocks


def to_markdown(heading, date, url, blocks):
    seen = {}
    for n, r, _ in blocks:
        if n and n != "Operator" and n not in seen: seen[n] = r
    out = [f"# {heading}", "", f"- Call date: {date.isoformat()}", f"- Source: {url}",
           "- Transcript provider (per source page): Quartr, via stockanalysis.com",
           f"- Retrieved: {dt.date.today().isoformat()}", "", "## Participants", ""]
    out += [f"- {n}" + (f" — {r}" if r else "") for n, r in seen.items()]
    out += ["", "## Transcript", ""]
    for n, r, paras in blocks:
        out += [f"**{n}**" + (f" ({r})" if r else ""), ""]
        for p in paras: out += [p, ""]
    return "\n".join(out)


# ---------------------------------------------------------------- tickers --
# Folder tickers whose stockanalysis.com listing differs (edit or override with FOLDER=ex:code)
ALIASES = {"SKHY": "krx:000660"}
SUFFIX_EXCHANGE = {"HK": "hkg", "KS": "krx", "KQ": "kosdaq", "T": "tyo", "L": "lon",
                   "TW": "tpe", "SS": "sha", "SZ": "she", "PA": "epa", "AS": "ams", "DE": "etr"}


def resolve_listing(folder_tk, listing):
    """Map a folder ticker to the site's listing: SKHY->krx:000660, 0700.HK->hkg:0700, BRK-B->BRK.B"""
    if listing.upper() != folder_tk:          # explicit FOLDER=listing given
        return listing
    if folder_tk in ALIASES:
        return ALIASES[folder_tk]
    m = re.fullmatch(r"([A-Z0-9]+)\.([A-Z]{1,2})", folder_tk)
    if m and m.group(2) in SUFFIX_EXCHANGE:
        return f"{SUFFIX_EXCHANGE[m.group(2)]}:{m.group(1)}"
    return folder_tk.replace("-", ".")          # US share classes, e.g. BRK-B -> BRK.B


def site_base(listing):
    """'ARM' -> /stocks/arm/ ; 'krx:000660' -> /quote/krx/000660/"""
    if ":" in listing:
        ex, tk = listing.split(":", 1)
        return f"{BASE}/quote/{ex.lower()}/{tk.lower()}/"
    return f"{BASE}/stocks/{listing.lower()}/"


def ticker_folder(root, ticker):
    hits = sorted(p for p in root.iterdir()
                  if p.is_dir() and re.match(rf"{re.escape(ticker)}(_|$)", p.name, re.I))
    return (hits[0] if hits else root / ticker.upper()) / "sources" / "Transcripts"


def load_tickers(args, root):
    items = list(args.tickers)
    f = Path(args.file) if args.file else (root / "transcript_tickers.txt" if not items else None)
    if f and f.is_file():
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line: items += line.replace(",", " ").split()
    if not items:          # fall back to every <TICKER>_... research folder under root
        items = sorted({p.name.split("_")[0].upper() for p in root.iterdir()
                        if p.is_dir() and "_" in p.name and not p.name.startswith((".", "_"))})
    pairs = []
    for it in items:
        folder_tk, _, listing = it.partition("=")
        folder_tk = folder_tk.upper()
        pairs.append((folder_tk, resolve_listing(folder_tk, listing or folder_tk)))
    return list(dict.fromkeys(pairs))


# ------------------------------------------------------------------ fetch --
def fetch_ticker(folder_tk, listing, root, args):
    out_dir = ticker_folder(root, folder_tk)
    idx_url = site_base(listing) + "transcripts/"
    try:
        idx = get(idx_url)
    except Exception as e:
        print(f"  ! could not open {idx_url} ({e}) — ticker not on stockanalysis.com?")
        return 0, 0, 1
    path = re.escape(re.sub(r"^https://stockanalysis\.com", "", idx_url))
    slugs = list(dict.fromkeys(re.findall(rf'{path}(\d+-[a-z0-9-]+)/', idx)))
    if not args.all_events:
        slugs = [s for s in slugs if re.search(r"-q\d-\d{4}$", s)]
    if not slugs:
        print(f"  ! no transcripts listed at {idx_url}")
        return 0, 0, 1
    cutoff = dt.date.today() - dt.timedelta(days=round(365.25 * args.years))
    saved = skipped = failed = 0
    for slug in slugs:
        qm = re.search(r"-q(\d)-(\d{4})$", slug)
        if qm and int(qm.group(2)) < cutoff.year - 2:      # clearly outside the window
            continue
        if qm and out_dir.is_dir() and not args.force:
            q, fy = qm.groups()
            ex = list(out_dir.glob(f"*Q{q}_FY{fy}_Earnings_Call_Transcript.md"))
            if ex:
                skipped += 1; continue
        url = f"{idx_url}{slug}/"
        try:
            title, date, company, blocks = extract(get(url))
        except Exception as e:
            print(f"  ! failed  {slug}: {e}"); failed += 1; continue
        if date is None or date < cutoff:
            continue
        who = f"{company} ({folder_tk})" if company else folder_tk
        if qm:
            q, fy = qm.groups()
            name = f"{date.isoformat()}_{folder_tk}_Q{q}_FY{fy}_Earnings_Call_Transcript.md"
            heading = f"{who} — Q{q} FY{fy} Earnings Call Transcript"
        else:
            label = re.sub(r"^\d+-", "", slug).replace("-", "_").title()
            name = f"{date.isoformat()}_{folder_tk}_{label}_Transcript.md"
            heading = f"{who} — {title} Transcript"
        dest = out_dir / name
        if dest.exists() and not args.force:
            skipped += 1; continue
        words = sum(len(" ".join(p).split()) for _, _, p in blocks)
        if args.dry_run:
            print(f"  · would save {name} ({words:,} words)")
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            dest.write_text(to_markdown(heading, date, url, blocks), encoding="utf-8")
            print(f"  + saved  {name}  ({len(blocks)} turns, {words:,} words)")
        saved += 1
        time.sleep(1)                                     # be polite to the site
    return saved, skipped, failed


def sweep_downloads(root, pairs, dry):
    moved = 0
    if not DOWNLOADS.is_dir():
        return 0
    for folder_tk, _ in pairs:
        for f in DOWNLOADS.glob(f"*_{folder_tk}_*Transcript*.md"):
            dest = ticker_folder(root, folder_tk) / f.name
            if dest.exists(): continue
            if not dry:
                dest.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(f), dest)
            print(f"  > moved  {f.name}  (from Downloads → {folder_tk})"); moved += 1
    return moved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--years", type=float, default=10)
    here = Path(__file__).resolve().parent
    # If the script sits inside a single research folder (has sources/), use its parent as root.
    ap.add_argument("--root", default=str(here.parent if (here / "sources").is_dir() else here))
    ap.add_argument("--all-events", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-downloads", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    pairs = load_tickers(args, root)
    if not pairs:
        ap.error("no tickers given and none found under " + str(root))
    print(f"Root: {root}\nTickers: {', '.join(f if f == l.upper() else f'{f}={l}' for f, l in pairs)}"
          f"\nWindow: last {args.years:g} years\n")
    summary = []
    for folder_tk, listing in pairs:
        print(f"[{folder_tk}] → {ticker_folder(root, folder_tk)}")
        s, k, f = fetch_ticker(folder_tk, listing, root, args)
        summary.append((folder_tk, s, k, f))
    moved = 0 if args.no_downloads else sweep_downloads(root, pairs, args.dry_run)
    print("\nSummary" + (" (dry run)" if args.dry_run else ""))
    for tk, s, k, f in summary:
        print(f"  {tk:<8} saved {s:>3}   already had {k:>3}   failed {f:>2}")
    if moved: print(f"  moved from Downloads: {moved}")


if __name__ == "__main__":
    sys.exit(main())
