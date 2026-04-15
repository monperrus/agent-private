#!/usr/bin/env python3
"""
Estimate the proportion of anonymous edits on English Wikipedia over the past month.
Uses the Wikimedia Analytics REST API.
"""
import urllib.request
import json
from datetime import datetime, timedelta

BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/edits/aggregate"
PROJECT = "en.wikipedia.org"
PAGE_TYPE = "all-page-types"
GRANULARITY = "monthly"


def fetch_edits(editor_type, start, end):
    url = f"{BASE_URL}/{PROJECT}/{editor_type}/{PAGE_TYPE}/{GRANULARITY}/{start}/{end}"
    req = urllib.request.Request(url, headers={"User-Agent": "WikipediaAnonEditsAnalysis/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get_last_month_range():
    today = datetime.utcnow()
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month
    last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)
    start = last_month_start.strftime("%Y%m%d00")
    end = last_month_end.strftime("%Y%m%d00")
    return start, end, last_month_start.strftime("%B %Y")


def main():
    start, end, month_label = get_last_month_range()
    print(f"Fetching edit statistics for {month_label}...")

    all_data = fetch_edits("all-editor-types", start, end)
    anon_data = fetch_edits("anonymous", start, end)

    total = all_data["items"][0]["results"][0]["edits"]
    anon = anon_data["items"][0]["results"][0]["edits"]
    proportion = anon / total * 100

    print(f"\nEnglish Wikipedia edit statistics for {month_label}:")
    print(f"  Total edits:                {total:>10,}")
    print(f"  Anonymous edits:            {anon:>10,}")
    print(f"  Proportion of anonymous:    {proportion:>9.2f}%")

    return total, anon, proportion, month_label


if __name__ == "__main__":
    main()
