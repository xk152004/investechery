#!/bin/bash
# Double-click in Finder: saves transcripts for every ticker in tickers.txt
# (or every <TICKER>_* research folder next to this file if tickers.txt is absent).
cd "$(dirname "$0")" && python3 fetch_transcripts.py "$@"
echo; read -n 1 -s -r -p "Press any key to close..."
