 
```
cd ~/Documents/Research/Equity
```

Batch collect company filings 
```
bash code/collect_filings.sh ADBE --years 10 -o . --transcripts-only
bash collect_filings.sh -f tickers.txt --years 10
python3 code/european_filing_collector.py ADYEN --dry-run
```

Batch collect earnings transcripts 
```
python3 fetch_transcripts.py GPN --years 10 --all-events
```

Generate report links 
```
python3 make_links.py stocks/ --sort created -o "links.md"
```


Copy over artifacts
```
bash sweep_artifacts.sh --apply
```
