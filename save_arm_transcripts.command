#!/bin/bash
# Double-click in Finder to fetch/save ARM earnings call transcripts into sources/Transcripts.
cd "$(dirname "$0")" && python3 fetch_arm_transcripts.py "$@"
echo; read -n 1 -s -r -p "Press any key to close..."
