#!/usr/bin/env bash
#
# collect_filings.sh — batch driver for sec_filing_collector.py
#
# Runs the collector once per ticker. The Python script creates one folder per
# company named  <TICKER>_<Company Name>  under the output root, and puts every
# downloaded document under that folder's  sources/  subfolder.
#
# Usage:
#   ./collect_filings.sh AAPL MSFT NVDA
#   ./collect_filings.sh -f tickers.txt
#   ./collect_filings.sh --years 5 --scope quick AAPL MSFT
#   echo "AAPL MSFT" | ./collect_filings.sh
#
# Options:
#   -f, --file FILE     read tickers from FILE (one per line or whitespace-
#                       separated; blank lines and #comments ignored)
#   -y, --years N       years of history          (default 10)
#   -s, --scope MODE    full | quick              (default full)
#   -o, --out DIR       output root               (default this script's folder)
#   -d, --subdir NAME   docs subfolder per company(default sources)
#       --no-form4      skip the slow Form 4 insider step
#   -h, --help          show this help
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR="$SCRIPT_DIR/sec_filing_collector.py"

YEARS=10
SCOPE="full"
OUT="$SCRIPT_DIR"
SUBDIR="sources"
NO_FORM4=""
TICKER_FILE=""
TICKERS=()

usage() { awk 'NR>1{ if ($0 !~ /^#/) exit; sub(/^# ?/,""); print }' "${BASH_SOURCE[0]}"; exit "${1:-0}"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)    TICKER_FILE="$2"; shift 2 ;;
    -y|--years)   YEARS="$2";       shift 2 ;;
    -s|--scope)   SCOPE="$2";       shift 2 ;;
    -o|--out)     OUT="$2";         shift 2 ;;
    -d|--subdir)  SUBDIR="$2";      shift 2 ;;
    --no-form4)   NO_FORM4="--no-form4"; shift ;;
    -h|--help)    usage 0 ;;
    -*)           echo "Unknown option: $1" >&2; usage 1 ;;
    *)            TICKERS+=("$1");  shift ;;
  esac
done

# ---- gather tickers -------------------------------------------------------
if [[ -n "$TICKER_FILE" ]]; then
  [[ -r "$TICKER_FILE" ]] || { echo "Cannot read ticker file: $TICKER_FILE" >&2; exit 1; }
  while read -r tok; do TICKERS+=("$tok"); done < <(sed 's/#.*//' "$TICKER_FILE" | tr ',' ' ' | tr -s '[:space:]' '\n' | grep -v '^$')
fi

# no args and no file -> read stdin if it is piped
if [[ ${#TICKERS[@]} -eq 0 && ! -t 0 ]]; then
  while read -r tok; do TICKERS+=("$tok"); done < <(sed 's/#.*//' | tr ',' ' ' | tr -s '[:space:]' '\n' | grep -v '^$')
fi

[[ ${#TICKERS[@]} -eq 0 ]] && { echo "No tickers given." >&2; usage 1; }
[[ -f "$COLLECTOR" ]] || { echo "Collector not found: $COLLECTOR" >&2; exit 1; }

PY="$(command -v python3 || command -v python)"
[[ -n "$PY" ]] || { echo "python3 not found on PATH" >&2; exit 1; }

mkdir -p "$OUT"
LOG_DIR="$OUT/_logs"; mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "=============================================================="
echo " Batch filing collection — ${#TICKERS[@]} ticker(s)"
echo " Output root : $OUT"
echo " Per company : <TICKER>_<Company Name>/$SUBDIR/"
echo " Years       : $YEARS      Scope: $SCOPE"
echo " Logs        : $LOG_DIR"
echo "=============================================================="

OK=(); FAILED=()
i=0
for T in "${TICKERS[@]}"; do
  T="$(echo "$T" | tr '[:lower:]' '[:upper:]')"
  i=$((i+1))
  LOG="$LOG_DIR/${T}_${STAMP}.log"
  echo
  echo "--------------------------------------------------------------"
  echo "[$i/${#TICKERS[@]}] $T"
  echo "--------------------------------------------------------------"
  if "$PY" "$COLLECTOR" "$T" \
        --out "$OUT" \
        --subdir "$SUBDIR" \
        --years "$YEARS" \
        --scope "$SCOPE" \
        $NO_FORM4 2>&1 | tee "$LOG"; then
    OK+=("$T")
  else
    # tee masks the exit status; recover it from PIPESTATUS
    if [[ ${PIPESTATUS[0]:-1} -eq 0 ]]; then OK+=("$T"); else FAILED+=("$T"); fi
  fi
  # be polite to SEC EDGAR between companies
  [[ $i -lt ${#TICKERS[@]} ]] && sleep 2
done

echo
echo "=============================================================="
echo " Summary"
echo "   Completed : ${#OK[@]}   ${OK[*]:-}"
echo "   Failed    : ${#FAILED[@]}   ${FAILED[*]:-}"
echo "=============================================================="
echo
echo "Company folders under $OUT:"
for T in "${OK[@]:-}"; do
  [[ -z "$T" ]] && continue
  find "$OUT" -maxdepth 1 -type d -name "${T}_*" -exec sh -c \
    'printf "  %s  (%s files in %s/)\n" "$(basename "$1")" "$(find "$1/$2" -type f 2>/dev/null | wc -l | tr -d " ")" "$2"' _ {} "$SUBDIR" \;
done

[[ ${#FAILED[@]} -eq 0 ]] || exit 1
