#!/usr/bin/env python3
"""
sec_filing_collector.py — build a research folder of official SEC filings for any
US-listed company (domestic filer or foreign private issuer).

Stdlib only. No pip install needed.

USAGE
-----
    python3 sec_filing_collector.py ARM
    python3 sec_filing_collector.py ARM --out ~/Documents/Research/Equity
    python3 sec_filing_collector.py MELI --years 5 --scope full
    python3 sec_filing_collector.py ARM --cik 1973239        # skip ticker lookup

    --out      parent folder; a subfolder <TICKER>_<Company> is created inside
    --years    lookback in years (default 10; the script never invents filings
               that do not exist, so a large value is safe)
    --scope    full (default) | quick
                 quick = annual reports + latest proxy + earnings releases only
    --no-form4 skip the insider-trading CSV (it is the slowest step)
    --email    contact address for the SEC User-Agent header (SEC requires one)

WHAT IT DOES
------------
1. Resolves ticker -> CIK from SEC's official company_tickers.json.
2. Reads https://data.sec.gov/submissions/CIK##########.json and detects filer
   status from the form types actually present (10-K => domestic, 20-F => FPI).
3. Downloads primary documents AND the EX-99 exhibits that carry the real
   content (press release, shareholder letter, earnings deck), sorting each into
   a category folder.
4. Parses every Form 4 XML into one Insider_Trading_Summary.csv.
5. Writes manifest.md describing what was collected and what is missing.

Re-running is safe and incremental: files already on disk at a plausible size are
skipped, and the manifest gains a refresh-log entry.

NOTES
-----
* SEC requires a descriptive User-Agent with a contact address and enforces
  10 requests/second. Both are handled here.
* EDGAR HTML is inline-XBRL tagged, so tags split phrases mid-sentence
  (<ix:nonNumeric>Compute</ix:nonNumeric> <ix:nonNumeric>Platform</ix:nonNumeric>).
  Strip tags before any text search downstream.
* Earnings-call transcripts and IR slide decks are NOT on EDGAR and are not
  collected here — see the manifest's gap list.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------

DEFAULT_EMAIL = "xk152004@gmail.com"
DEFAULT_OUT = "~/Documents/Research/Equity"

SEC_RATE_LIMIT_SLEEP = 0.12  # SEC allows 10 req/sec
TIMEOUT = 60

FOLDERS = [
    "Annual_Reports",
    "Quarterly_and_Interim_Reports",
    "Transcripts",
    "Proxy_and_Governance",
    "Insider_Trading",
    "Earnings_Releases",
    "Earnings_Presentations",
    "Investor_Day_and_CMD",
    "Shareholder_Letters",
    "Material_Events",
    "Conference_Presentations",
    "Other_Key_Documents",
]

# Minimum plausible byte size per category. Anything smaller is treated as a
# broken download (paywall wrapper / anti-bot page) and re-fetched.
MIN_SIZE = {
    "Annual_Reports": 400_000,
    "Quarterly_and_Interim_Reports": 100_000,
    "Earnings_Releases": 2_000,
    "Shareholder_Letters": 10_000,
    "Material_Events": 1_000,
    "Proxy_and_Governance": 100_000,
    "Other_Key_Documents": 10_000,
    "Earnings_Presentations": 2_000,
}

BAD_CONTENT = re.compile(
    rb"just a moment|cloudflare|verify you are human|enable javascript to continue"
    rb"|isAccessibleForFree\"?\s*:\s*\"?False",
    re.I,
)

# Form 4 transaction codes worth annotating
CODE_MEANING = {
    "P": "Open-market purchase",
    "S": "Open-market sale",
    "A": "Grant/award",
    "M": "Option exercise",
    "F": "Tax withholding",
    "G": "Gift",
    "C": "Conversion",
    "D": "Disposition to issuer",
    "X": "Option exercise (in-the-money)",
}
NON_DISCRETIONARY = {"A", "F", "G", "C", "D"}


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

class Fetcher:
    def __init__(self, user_agent: str):
        self.ua = user_agent
        self.n_requests = 0
        self.n_bytes = 0

    def get(self, url: str, retries: int = 3) -> bytes:
        last = None
        for attempt in range(retries):
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.ua,
                    "Accept-Encoding": "gzip, deflate",
                    "Accept": "*/*",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                self.n_requests += 1
                self.n_bytes += len(raw)
                time.sleep(SEC_RATE_LIMIT_SLEEP)
                return raw
            except urllib.error.HTTPError as e:
                last = e
                if e.code == 404:
                    raise
                time.sleep(1.5 * (attempt + 1))
            except Exception as e:  # noqa: BLE001 - network flakiness
                last = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"failed after {retries} attempts: {url} ({last})")

    def get_json(self, url: str):
        return json.loads(self.get(url).decode("utf-8", "replace"))


# ----------------------------------------------------------------------------
# EDGAR helpers
# ----------------------------------------------------------------------------

def resolve_cik(fetch: Fetcher, ticker: str) -> tuple[str, str]:
    """Return (cik_int_str, company_title) for a ticker."""
    data = fetch.get_json("https://www.sec.gov/files/company_tickers.json")
    t = ticker.upper()
    for row in data.values():
        if row["ticker"].upper() == t:
            return str(row["cik_str"]), row["title"]
    raise SystemExit(
        f"Ticker {ticker!r} not found in SEC's company_tickers.json. "
        f"Pass --cik explicitly if the company files under a different symbol."
    )


def load_submissions(fetch: Fetcher, cik: str) -> dict:
    """Full submission history, following the older-filings shards."""
    padded = cik.zfill(10)
    sub = fetch.get_json(f"https://data.sec.gov/submissions/CIK{padded}.json")
    recent = sub["filings"]["recent"]
    merged = {k: list(v) for k, v in recent.items()}
    for shard in sub["filings"].get("files", []):
        extra = fetch.get_json(f"https://data.sec.gov/submissions/{shard['name']}")
        for k, v in extra.items():
            merged.setdefault(k, []).extend(v)
    sub["_merged"] = merged
    return sub


def iter_filings(sub: dict):
    m = sub["_merged"]
    n = len(m["form"])
    for i in range(n):
        yield {
            "form": m["form"][i],
            "filingDate": m["filingDate"][i],
            "reportDate": (m.get("reportDate") or [""] * n)[i] or "",
            "accession": m["accessionNumber"][i],
            "primaryDocument": (m.get("primaryDocument") or [""] * n)[i] or "",
            "items": (m.get("items") or [""] * n)[i] or "",
        }


def archive_base(cik: str, accession: str) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
        f"{accession.replace('-', '')}/"
    )


def detect_filer_status(forms: set[str]) -> str:
    if "10-K" in forms:
        return "US-domestic filer"
    if "20-F" in forms:
        return "Foreign private issuer (FPI)"
    if "40-F" in forms:
        return "Canadian MJDS filer"
    return "Unknown / no annual report on EDGAR"


QUARTER_ENDS = {"03-31", "06-30", "09-30", "12-31"}


def fiscal_label(report_date: str, fy_end: str) -> str:
    """Map a period-end date to FY/quarter given a fiscal year end like '0331'."""
    try:
        d = datetime.strptime(report_date, "%Y-%m-%d").date()
    except ValueError:
        return report_date
    fy_month = int(fy_end[:2]) if fy_end and len(fy_end) == 4 else 12
    # Fiscal year is the calendar year in which the FY *ends*.
    fy = d.year if d.month <= fy_month else d.year + 1
    months_in = (d.month - fy_month - 1) % 12 + 1
    q = (months_in + 2) // 3
    return f"FY{fy}_Q{q}"


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")


# ----------------------------------------------------------------------------
# Download planning
# ----------------------------------------------------------------------------

def classify_exhibit(filename: str) -> str | None:
    """Map an EX-99.x exhibit filename to a category folder."""
    f = filename.lower()
    if not re.match(r"^(ex|exhibit)", f):
        return None
    if re.search(r"99[._-]?1|991", f):
        return "Earnings_Releases"
    if re.search(r"99[._-]?2|992", f):
        return "Shareholder_Letters"
    if re.search(r"99[._-]?[3-9]|99[3-9]", f):
        return "Earnings_Presentations"
    return None


def build_plan(fetch: Fetcher, cik: str, sub: dict, cutoff: str, scope: str) -> list[dict]:
    """Return a list of {url, folder, filename, form, filed, period} download jobs."""
    fy_end = sub.get("fiscalYearEnd", "1231") or "1231"
    plan: list[dict] = []
    seen_proxy = False

    filings = [f for f in iter_filings(sub) if f["filingDate"] >= cutoff]
    filings.sort(key=lambda f: f["filingDate"], reverse=True)

    for f in filings:
        form, acc, doc = f["form"], f["accession"], f["primaryDocument"]
        filed, period, items = f["filingDate"], f["reportDate"], f["items"]
        if not doc:
            continue
        base = archive_base(cik, acc)
        ext = os.path.splitext(doc)[1] or ".html"
        if ext.lower() in (".htm",):
            ext = ".html"

        def job(folder, fname, url=None, note=""):
            plan.append({
                "url": url or (base + doc),
                "folder": folder,
                "filename": safe(fname),
                "form": form,
                "filed": filed,
                "period": period,
                "note": note,
            })

        # --- Annual reports -------------------------------------------------
        if form in ("10-K", "20-F", "40-F", "10-K/A", "20-F/A"):
            fy = fiscal_label(period, fy_end).split("_")[0] if period else filed[:4]
            job("Annual_Reports", f"{fy}_{form}_{filed}{ext}")
            continue

        # --- Proxy ----------------------------------------------------------
        if form in ("DEF 14A", "DEFA14A"):
            if scope == "quick" and seen_proxy:
                continue
            seen_proxy = True
            job("Proxy_and_Governance", f"{filed}_{safe(form)}{ext}")
            continue

        # --- Quarterlies ----------------------------------------------------
        if form in ("10-Q", "10-Q/A"):
            if scope == "quick":
                continue
            lbl = fiscal_label(period, fy_end) if period else filed
            job("Quarterly_and_Interim_Reports", f"{lbl}_{form}_{filed}{ext}")
            continue

        # --- Current reports: 8-K (domestic) and 6-K (FPI) -------------------
        if form in ("8-K", "6-K", "8-K/A", "6-K/A"):
            is_interim = (
                form.startswith("6-K")
                and period
                and period != filed
                and period[5:] in QUARTER_ENDS
            )
            if is_interim:
                if scope != "quick":
                    lbl = fiscal_label(period, fy_end)
                    job("Quarterly_and_Interim_Reports",
                        f"{lbl}_{period}_Interim_6-K{ext}")
            elif form.startswith("8-K"):
                if "2.02" in items:
                    job("Earnings_Releases", f"{filed}_8-K_Item2.02{ext}")
                elif any(c in items for c in ("2.01", "5.02", "1.01")):
                    job("Material_Events", f"{filed}_8-K_{safe(items)[:40]}{ext}")
                elif scope != "quick":
                    job("Other_Key_Documents", f"{filed}_8-K{ext}")
            else:  # non-interim 6-K cover page
                if scope != "quick":
                    job("Material_Events", f"{filed}_6-K{ext}")

            # Exhibits carry the actual content for both 8-K and 6-K.
            if scope == "quick" and not (form.startswith("6-K") or "2.02" in items):
                continue
            try:
                idx = fetch.get_json(base + "index.json")
            except Exception:
                continue
            for item in idx.get("directory", {}).get("item", []):
                nm = item.get("name", "")
                if not re.search(r"\.(htm|html|pdf)$", nm, re.I):
                    continue
                folder = classify_exhibit(nm)
                if not folder:
                    continue
                if scope == "quick" and folder != "Earnings_Releases":
                    continue
                lbl = fiscal_label(period, fy_end) if period and period != filed else filed
                tag = {"Earnings_Releases": "Press_Release",
                       "Shareholder_Letters": "Shareholder_Letter",
                       "Earnings_Presentations": "Presentation"}[folder]
                e = os.path.splitext(nm)[1].replace(".htm", ".html")
                job(folder, f"{filed}_{lbl}_{tag}{e}", url=base + nm)
            continue

        # --- IPO / registration docs (high value for recent listings) --------
        if form in ("F-1", "S-1", "424B4", "424B1"):
            if scope != "quick":
                job("Other_Key_Documents", f"{filed}_{safe(form)}_Prospectus{ext}")
            continue

    # De-duplicate by destination path, keeping the first (newest) occurrence.
    out, seen = [], set()
    for j in plan:
        key = (j["folder"], j["filename"])
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


# ----------------------------------------------------------------------------
# Form 4 -> CSV
# ----------------------------------------------------------------------------

def _txt(node, path, default=""):
    el = node.find(path)
    if el is None:
        return default
    v = el.find("value")
    if v is not None:
        return (v.text or "").strip()
    return (el.text or "").strip()


def parse_form4(xml_bytes: bytes, filed: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    owner = root.find(".//reportingOwner")
    name = _txt(owner, "reportingOwnerId/rptOwnerName") if owner is not None else ""
    rel = owner.find("reportingOwnerRelationship") if owner is not None else None
    roles = []
    if rel is not None:
        if _txt(rel, "isDirector") in ("1", "true"):
            roles.append("Director")
        if _txt(rel, "isOfficer") in ("1", "true"):
            roles.append(_txt(rel, "officerTitle") or "Officer")
        if _txt(rel, "isTenPercentOwner") in ("1", "true"):
            roles.append("10% owner")
    role = "; ".join(roles)

    footnotes = " ".join(
        (fn.text or "") for fn in root.findall(".//footnotes/footnote")
    ).lower()
    plan_flag = "10b5-1 plan" if "10b5-1" in footnotes else ""

    rows = []
    for deriv, tag in ((False, "nonDerivativeTransaction"),
                       (True, "derivativeTransaction")):
        for t in root.findall(f".//{tag}"):
            code = _txt(t, "transactionCoding/transactionCode")
            shares = _txt(t, "transactionAmounts/transactionShares")
            price = _txt(t, "transactionAmounts/transactionPricePerShare")
            ad = _txt(t, "transactionAmounts/transactionAcquiredDisposedCode")
            after = _txt(t, "postTransactionAmounts/sharesOwnedFollowingTransaction")
            tdate = _txt(t, "transactionDate")
            try:
                sh = float(shares) if shares else 0.0
                pr = float(price) if price else 0.0
                total = sh * pr
            except ValueError:
                sh, pr, total = 0.0, 0.0, 0.0

            notes = []
            if deriv:
                notes.append("Derivative")
            if plan_flag:
                notes.append(plan_flag)
            if code == "F":
                notes.append("Tax withholding")
            if code in NON_DISCRETIONARY:
                notes.append("Non-discretionary")

            rows.append({
                "Filing Date": filed,
                "Trade Date": tdate,
                "Insider Name": name,
                "Title/Role": role,
                "Transaction Type": f"{code} - {CODE_MEANING.get(code, 'Other')}"
                                    f"{' (' + ('Acquired' if ad == 'A' else 'Disposed') + ')' if ad else ''}",
                "Price": f"{pr:.4f}" if pr else "",
                "Shares": f"{sh:.0f}" if sh else shares,
                "Holdings After": after,
                "Total $": f"{total:.0f}" if total else "",
                "Notes": "; ".join(notes),
            })
    return rows


def collect_form4(fetch: Fetcher, cik: str, sub: dict, cutoff: str,
                  out_dir: str, log) -> tuple[int, int]:
    jobs = [f for f in iter_filings(sub)
            if f["form"] in ("4", "4/A") and f["primaryDocument"].endswith(".xml")]
    jobs.sort(key=lambda f: f["filingDate"], reverse=True)
    if not jobs:
        return 0, 0

    all_rows: list[dict] = []
    for i, f in enumerate(jobs, 1):
        url = archive_base(cik, f["accession"]) + f["primaryDocument"]
        try:
            rows = parse_form4(fetch.get(url), f["filingDate"])
        except Exception as e:  # noqa: BLE001
            log(f"    ! Form 4 {f['accession']}: {e}")
            continue
        if f["form"] == "4/A":
            for r in rows:
                r["Notes"] = ("Amended; " + r["Notes"]).strip("; ")
        all_rows.extend(rows)
        if i % 25 == 0:
            log(f"    ... {i}/{len(jobs)} Form 4s parsed")

    all_rows.sort(key=lambda r: (r["Filing Date"], r["Trade Date"]), reverse=True)

    # Flag cluster sales: 3+ distinct insiders disposing in the same ISO week.
    weeks: dict[str, set[str]] = {}
    for r in all_rows:
        if "Disposed" in r["Transaction Type"]:
            try:
                y, w, _ = datetime.strptime(r["Trade Date"], "%Y-%m-%d").isocalendar()
                weeks.setdefault(f"{y}-W{w}", set()).add(r["Insider Name"])
            except ValueError:
                pass
    hot = {k for k, v in weeks.items() if len(v) >= 3}
    for r in all_rows:
        if "Disposed" in r["Transaction Type"]:
            try:
                y, w, _ = datetime.strptime(r["Trade Date"], "%Y-%m-%d").isocalendar()
                if f"{y}-W{w}" in hot:
                    r["Notes"] = (r["Notes"] + "; Cluster sale").strip("; ")
            except ValueError:
                pass

    cols = ["Filing Date", "Trade Date", "Insider Name", "Title/Role",
            "Transaction Type", "Price", "Shares", "Holdings After",
            "Total $", "Notes"]

    dest = os.path.join(out_dir, "Insider_Trading")
    os.makedirs(dest, exist_ok=True)

    full = os.path.join(dest, "Insider_Trading_Full_History.csv")
    with open(full, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(all_rows)

    windowed = [r for r in all_rows if r["Filing Date"] >= cutoff]
    summ = os.path.join(dest, "Insider_Trading_Summary.csv")
    with open(summ, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(windowed)

    return len(windowed), len(all_rows)


# ----------------------------------------------------------------------------
# Manifest
# ----------------------------------------------------------------------------

def write_manifest(out_dir, docs_dir, subdir, sub, ticker, cik, filer_status,
                   scope, years, cutoff, results, form4_counts, fetch, refreshed):
    path = os.path.join(out_dir, "manifest.md")
    today = date.today().isoformat()

    prior = ""
    initial = today
    if os.path.exists(path):
        prior = open(path, encoding="utf-8").read()
        m = re.search(r"Initial collection date.*?(\d{4}-\d{2}-\d{2})", prior)
        if m:
            initial = m.group(1)

    by_folder: dict[str, list] = {}
    for r in results:
        by_folder.setdefault(r["folder"], []).append(r)

    ok = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] not in ("ok", "skipped")]

    L = []
    A = L.append
    A(f"# {sub.get('name', ticker)} — Filing Collection Manifest\n")
    A("## Company Information\n")
    addr = (sub.get("addresses", {}) or {}).get("business", {}) or {}
    A(f"- **Legal name:** {sub.get('name','')}")
    A(f"- **Ticker:** {ticker}  |  **Exchanges:** {', '.join(sub.get('exchanges') or []) or 'n/a'}")
    A(f"- **CIK:** {int(cik)} (padded {str(cik).zfill(10)})")
    A(f"- **Filer status:** {filer_status}")
    A(f"- **Fiscal year end:** {sub.get('fiscalYearEnd','?')} (MMDD)")
    A(f"- **SIC:** {sub.get('sic','')} — {sub.get('sicDescription','')}")
    A(f"- **Country of incorporation:** {sub.get('stateOfIncorporationDescription') or sub.get('stateOfIncorporation') or 'n/a'}")
    A(f"- **HQ:** {addr.get('city','')}, {addr.get('stateOrCountryDescription','')}")
    A(f"- **IR site:** {sub.get('website') or 'see company IR page'}\n")

    A("## Collection Parameters\n")
    A(f"- **Scope:** {scope}")
    A(f"- **Lookback:** {years} years (cutoff {cutoff})")
    A(f"- **Language policy:** English (EDGAR filings are English by rule)")
    A(f"- **Initial collection date:** {initial}")
    A(f"- **Last refresh date:** {today}\n")

    if failed:
        A("## Critical Findings\n")
        for r in failed:
            A(f"- **FAILED** `{r['folder']}/{r['filename']}` — {r['status']}")
        A("")

    A(f"All documents live under `{subdir}/`.\n")
    A("## Collection Summary\n")
    for folder in FOLDERS:
        rows = by_folder.get(folder) or []
        disk = os.path.join(docs_dir, folder)
        on_disk = sorted(os.listdir(disk)) if os.path.isdir(disk) else []
        if not rows and not on_disk:
            continue
        A(f"### {subdir}/{folder}  ({len(on_disk)} files)\n")
        A("| Period / Date | Form | Filename | Size | Source | Status |")
        A("|---|---|---|---|---|---|")
        for r in sorted(rows, key=lambda x: x["filename"], reverse=True):
            size = f"{r['size']:,} B" if r.get("size") else "—"
            A(f"| {r.get('period') or r.get('filed','')} | {r.get('form','')} "
              f"| `{r['filename']}` | {size} | SEC EDGAR | {r['status']} |")
        A("")

    A("## Insider Trading\n")
    if form4_counts:
        win, tot = form4_counts
        A(f"- `{subdir}/Insider_Trading/Insider_Trading_Summary.csv` — {win} transactions within the lookback window")
        A(f"- `{subdir}/Insider_Trading/Insider_Trading_Full_History.csv` — {tot} transactions, full available history")
        A("- Parsed directly from SEC Form 4 XML (not a third-party aggregator).")
        A("- `Notes` flags: Derivative, Amended, 10b5-1 plan, Tax withholding, "
          "Non-discretionary, Cluster sale (3+ insiders disposing in one week).\n")
    else:
        A("- No Form 4 filings found. Many foreign private issuers are exempt "
          "from Section 16 reporting.\n")

    A("## Download Method Tally\n")
    A(f"- Downloaded this run: **{len(ok)}**")
    A(f"- Already present, skipped: **{len(skipped)}**")
    A(f"- Failed: **{len(failed)}**")
    A(f"- HTTP requests: {fetch.n_requests}  |  Bytes transferred: {fetch.n_bytes:,}")
    A("- Source: SEC EDGAR only (`data.sec.gov` for enumeration, "
      "`www.sec.gov/Archives` for documents), via Python urllib.\n")

    A("## Coverage Assessment\n")
    for folder in FOLDERS:
        disk = os.path.join(docs_dir, folder)
        n = len(os.listdir(disk)) if os.path.isdir(disk) else 0
        A(f"- {folder.replace('_',' ')}: {n}")
    A("")
    A("**Known gaps — not available on EDGAR:**\n")
    A("- Earnings-call **transcripts** (Motley Fool / Quartr / Seeking Alpha / IR site)")
    A("- **Investor Day / Capital Markets Day decks** and PDF earnings presentations "
      "hosted on the company IR site")
    A("- Sell-side estimates, consensus, and any third-party research (out of scope "
      "by design — official sources only)\n")

    A("## Research Readiness\n")
    A("**Sufficient for:**")
    A("- Business-model and segment analysis, risk factors, accounting policies "
      "(annual reports)")
    A("- Multi-year financial history and quarterly seasonality (interims + annuals)")
    A("- Management narrative tracking (shareholder letters + press releases)")
    A("- Insider alignment and capital-allocation signals (Form 4 CSV)\n")
    A("**Not yet sufficient for:**")
    A("- Q&A tone and analyst pushback — needs transcripts")
    A("- Management's own framing of long-term targets — needs Investor Day decks\n")

    A("## iXBRL Note\n")
    A("EDGAR HTML documents are inline-XBRL tagged. Tags split phrases mid-sentence, "
      "so a naive `grep \"Compute Platform\"` returns near-zero hits. **Strip tags "
      "before any text search.** Quick strip:\n")
    A("```bash")
    A("python3 -c \"import re,sys;print(re.sub(r'<[^>]+>',' ',open(sys.argv[1],encoding='utf-8',errors='replace').read()))\" FILE.html > FILE.txt")
    A("```\n")

    A("## Refresh Log\n")
    if refreshed:
        A(f"- **{today}** — refresh: {len(ok)} added, {len(skipped)} already present.")
        for r in ok[:40]:
            A(f"  - `{r['folder']}/{r['filename']}`")
    else:
        A(f"- **{today}** — initial collection: {len(ok)} files downloaded.")
    A("")

    if prior:
        m = re.search(r"^## Refresh Log\n(.*)$", prior, re.S | re.M)
        if m:
            old = m.group(1).strip()
            old = "\n".join(l for l in old.splitlines() if l.strip().startswith("- **"))
            if old:
                A("<!-- previous runs -->")
                A(old)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    return path


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Collect SEC filings into a research folder.")
    p.add_argument("ticker")
    p.add_argument("--cik", default=None)
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--years", type=int, default=10)
    p.add_argument("--scope", choices=["full", "quick"], default="full")
    p.add_argument("--subdir", default="sources",
                   help="subfolder inside the company folder that holds all "
                        "downloaded documents (default: sources)")
    p.add_argument("--no-form4", action="store_true")
    p.add_argument("--email", default=DEFAULT_EMAIL)
    args = p.parse_args()

    ticker = args.ticker.upper()
    fetch = Fetcher(f"{ticker} research collector {args.email}")

    def log(msg=""):
        print(msg, flush=True)

    log(f"== SEC filing collector — {ticker} ==")

    if args.cik:
        cik, title = str(int(args.cik)), ticker
    else:
        log("Resolving CIK...")
        cik, title = resolve_cik(fetch, ticker)

    log(f"Loading submission history for CIK {cik}...")
    sub = load_submissions(fetch, cik)
    title = sub.get("name", title)
    forms = {f["form"] for f in iter_filings(sub)}
    filer_status = detect_filer_status(forms)
    log(f"  {title}")
    log(f"  Filer status: {filer_status}   FY end: {sub.get('fiscalYearEnd','?')}")

    company_dir = f"{ticker}_{safe(title)}"
    out_dir = os.path.join(os.path.expanduser(args.out), company_dir)
    docs_dir = os.path.join(out_dir, args.subdir) if args.subdir else out_dir
    refreshed = os.path.exists(os.path.join(out_dir, "manifest.md"))
    for f in FOLDERS:
        os.makedirs(os.path.join(docs_dir, f), exist_ok=True)
    log(f"  Output: {docs_dir}" + ("   (refresh)" if refreshed else "   (new)"))

    cutoff = (date.today() - timedelta(days=365 * args.years + 90)).isoformat()
    log(f"\nBuilding download plan (cutoff {cutoff}, scope {args.scope})...")
    plan = build_plan(fetch, cik, sub, cutoff, args.scope)
    log(f"  {len(plan)} documents queued\n")

    results = []
    for i, j in enumerate(plan, 1):
        dest = os.path.join(docs_dir, j["folder"], j["filename"])
        floor = MIN_SIZE.get(j["folder"], 1_000)
        if os.path.exists(dest) and os.path.getsize(dest) >= floor:
            j.update(status="skipped", size=os.path.getsize(dest))
            results.append(j)
            continue
        try:
            data = fetch.get(j["url"])
            if len(data) < floor or BAD_CONTENT.search(data[:4000]):
                raise RuntimeError(
                    f"suspicious payload ({len(data)} bytes, floor {floor})")
            with open(dest, "wb") as fh:
                fh.write(data)
            j.update(status="ok", size=len(data))
            log(f"  [{i}/{len(plan)}] {j['folder']}/{j['filename']}  "
                f"{len(data):,} B")
        except Exception as e:  # noqa: BLE001
            j.update(status=f"error: {e}", size=0)
            log(f"  [{i}/{len(plan)}] FAILED {j['filename']}: {e}")
        results.append(j)

    form4_counts = None
    if not args.no_form4 and args.scope == "full":
        log("\nParsing Form 4 insider filings (this is the slow step)...")
        try:
            form4_counts = collect_form4(fetch, cik, sub, cutoff, docs_dir, log)
            if form4_counts[1]:
                log(f"  {form4_counts[0]} in window / {form4_counts[1]} total transactions")
            else:
                log("  No Form 4 filings found (common for foreign private issuers).")
                form4_counts = None
        except Exception as e:  # noqa: BLE001
            log(f"  Form 4 step failed: {e}")

    if not form4_counts:
        na = os.path.join(docs_dir, "Insider_Trading", "NOT_AVAILABLE.md")
        if not os.path.exists(na):
            with open(na, "w", encoding="utf-8") as fh:
                fh.write(
                    "# Insider trading data not collected\n\n"
                    "No Form 4 filings were found for this issuer, or the step was "
                    "skipped. Many foreign private issuers are exempt from Section 16 "
                    "reporting; local equivalents (UK PDMR notifications, AMF "
                    "declarations, BaFin Eigengeschafte) must be looked up manually.\n")

    log("\nWriting manifest...")
    mpath = write_manifest(out_dir, docs_dir, args.subdir or ".", sub, ticker, cik,
                           filer_status, args.scope, args.years, cutoff, results,
                           form4_counts, fetch, refreshed)

    ok = sum(1 for r in results if r["status"] == "ok")
    sk = sum(1 for r in results if r["status"] == "skipped")
    bad = len(results) - ok - sk
    log(f"\nDone. {ok} downloaded, {sk} already present, {bad} failed.")
    log(f"Manifest: {mpath}")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
