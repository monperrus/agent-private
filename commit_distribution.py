"""
Compute distribution of number of commits per year on GitHub (2023, 2024, 2025).

Methodology:
- Sample ~1,500 GitHub repositories using the Search API with diverse queries
  (varying star ranges, languages, pushed-date ranges) for broad coverage.
- For each repo, count commits per year using the REST API:
  GET /repos/{owner}/{repo}/commits?since=...&until=...&per_page=1
  The last-page number from the Link header gives the total count.
- Compute distribution statistics with numpy.

Usage:
  GITHUB_TOKEN=<token> python commit_distribution.py
"""

import os
import re
import time
import random
import requests
import numpy as np

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

SEARCH_QUERIES = [
    "stars:1..5 pushed:2023-01-01..2023-12-31 language:python",
    "stars:1..5 pushed:2024-01-01..2024-12-31 language:javascript",
    "stars:1..5 pushed:2025-01-01..2025-12-31 language:java",
    "stars:5..20 pushed:2023-06-01..2023-12-31",
    "stars:5..20 pushed:2024-06-01..2024-12-31",
    "stars:5..20 pushed:2025-01-01..2025-06-30",
    "stars:20..100 pushed:2023-01-01..2023-06-30",
    "stars:20..100 pushed:2024-01-01..2024-06-30",
    "stars:20..100 pushed:2025-06-01..2025-12-31",
    "stars:100..500 pushed:2023-01-01..2023-12-31",
    "stars:100..500 pushed:2024-01-01..2024-12-31",
    "stars:100..500 pushed:2025-01-01..2025-12-31",
    "stars:500..2000 pushed:2024-01-01..2024-12-31",
    "stars:2000..10000 pushed:2023-01-01..2024-12-31",
    "stars:1..3 pushed:2025-01-01..2025-12-31 language:go",
    "stars:1..3 pushed:2024-01-01..2024-12-31 language:typescript",
    "stars:1..3 pushed:2023-01-01..2023-12-31 language:rust",
    "stars:3..10 pushed:2025-01-01..2025-12-31 language:c",
    "stars:3..10 pushed:2024-01-01..2024-12-31 language:cpp",
    "stars:3..10 pushed:2023-01-01..2023-12-31 language:ruby",
]


def search_repos(query, per_page=100, max_pages=2):
    repos = []
    for page in range(1, max_pages + 1):
        r = requests.get(
            "https://api.github.com/search/repositories",
            headers=HEADERS,
            params={"q": query, "per_page": per_page, "page": page, "sort": "updated"},
            timeout=15,
        )
        if r.status_code != 200:
            break
        items = r.json().get("items", [])
        for item in items:
            parts = item["full_name"].split("/")
            if len(parts) == 2:
                repos.append(tuple(parts))
        if len(items) < per_page:
            break
        time.sleep(0.3)
    return repos


def get_commit_count(owner, repo, year):
    """Return number of commits in `year` for a repo, or None on error."""
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        headers=HEADERS,
        params={
            "since": f"{year}-01-01T00:00:00Z",
            "until": f"{year}-12-31T23:59:59Z",
            "per_page": 1,
        },
        timeout=15,
    )
    if r.status_code == 409:  # empty repository
        return 0
    if r.status_code != 200:
        return None
    link = r.headers.get("Link", "")
    if "rel=\"last\"" in link:
        m = re.search(r"page=(\d+)>; rel=\"last\"", link)
        if m:
            return int(m.group(1))
    data = r.json()
    return len(data) if isinstance(data, list) else None


def print_stats(label, data):
    arr = np.array(data)
    n = len(arr)
    active = arr[arr >= 1]
    print(f"\n=== {label} (n={n}) ===")
    print(f"  Min:          {int(np.min(arr))}")
    print(f"  P10:          {np.percentile(arr, 10):.1f}")
    print(f"  P25:          {np.percentile(arr, 25):.1f}")
    print(f"  Median (P50): {np.median(arr):.1f}")
    print(f"  Mean:         {np.mean(arr):.1f}")
    print(f"  P75:          {np.percentile(arr, 75):.1f}")
    print(f"  P90:          {np.percentile(arr, 90):.1f}")
    print(f"  P95:          {np.percentile(arr, 95):.1f}")
    print(f"  P99:          {np.percentile(arr, 99):.1f}")
    print(f"  Max:          {int(np.max(arr))}")
    print(f"  Repos with 0 commits: {int(np.sum(arr == 0))} ({100*np.mean(arr == 0):.1f}%)")
    if len(active):
        print(f"  Active repos (n={len(active)}):")
        print(f"    Median: {np.median(active):.1f}")
        print(f"    P90:    {np.percentile(active, 90):.1f}")


def main():
    random.seed(42)
    all_repos = set()
    for q in SEARCH_QUERIES:
        all_repos.update(search_repos(q))
        time.sleep(0.5)
    repos = random.sample(list(all_repos), min(1500, len(all_repos)))
    print(f"Sampled {len(repos)} repos")

    results = {2023: [], 2024: [], 2025: []}
    for i, (owner, repo) in enumerate(repos):
        for year in [2023, 2024, 2025]:
            count = get_commit_count(owner, repo, year)
            if count is not None:
                results[year].append(count)
        if (i + 1) % 100 == 0:
            print(f"Processed {i+1}/{len(repos)}")
        time.sleep(0.05)

    for year in [2023, 2024, 2025]:
        print_stats(f"{year} — commits per repository", results[year])


if __name__ == "__main__":
    main()
