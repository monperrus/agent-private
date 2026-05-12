#!/usr/bin/env python3
"""Retry LOC counting for repos that timed out in count_loc_parallel.py.

Runs cloc sequentially with a much longer timeout (300 s) and appends/
overrides entries in an existing loc_results.tsv.

Usage:
    python3 count_loc_retry.py repo/name [repo/name ...]
    # or edit RETRY_REPOS below and run without arguments

Dependencies: git, cloc (apt install cloc)
"""

import subprocess
import json
import os
import sys

# Benchmark commit hashes for the repos that commonly time out
ALL_COMMITS = {
    "ffmpeg/ffmpeg": "360a402",
    "johnkerl/miller": "8d85b46",
    "gromacs/gromacs": "665ea4c",
    "duckdb/duckdb": "bdb65ec",
    "php/php-src": "c891263",
    "osgeo/gdal": "0847f12",
}

CLOC_TIMEOUT = 300   # seconds
CLONE_TIMEOUT = 300
OUTFILE = "loc_results.tsv"


def count_loc(repo: str, commit: str) -> tuple[int, str]:
    tmpdir = f"/tmp/pb2_{repo.replace('/', '_')}"
    try:
        if not os.path.exists(tmpdir):
            print(f"  Cloning {repo}...")
            r = subprocess.run(
                ["git", "clone", "--depth=1", "--no-tags", "-q",
                 f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, timeout=CLONE_TIMEOUT
            )
            if r.returncode != 0:
                return -1, "clone_failed"

        print(f"  Running cloc on {repo} (may take a while)...")
        r2 = subprocess.run(
            ["cloc", tmpdir, "--quiet", "--json"],
            capture_output=True, text=True, timeout=CLOC_TIMEOUT
        )
        data = json.loads(r2.stdout)
        code = data.get("SUM", {}).get("code", 0)
        return code, "ok"
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    except Exception as e:
        return -1, str(e)
    finally:
        subprocess.run(["rm", "-rf", tmpdir], capture_output=True)


def main():
    repos_to_retry = sys.argv[1:] if len(sys.argv) > 1 else list(ALL_COMMITS.keys())

    # Read existing results
    existing: dict[str, tuple[str, int]] = {}
    if os.path.exists(OUTFILE):
        with open(OUTFILE) as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    existing[parts[0]] = (parts[1], int(parts[2]))

    # Run retries
    for repo in repos_to_retry:
        if repo not in ALL_COMMITS:
            print(f"Unknown repo '{repo}', skipping")
            continue
        commit = ALL_COMMITS[repo]
        print(f"\n{repo} @ {commit}")
        code, status = count_loc(repo, commit)
        if status == "ok":
            print(f"  => {code:,} lines")
            existing[repo] = (commit, code)
        else:
            print(f"  => FAILED ({status})")

    # Write merged results
    with open(OUTFILE, "w") as f:
        f.write("repository\tcommit\tcode_lines_cloc\n")
        for repo in sorted(existing):
            commit, code = existing[repo]
            f.write(f"{repo}\t{commit}\t{code}\n")

    print(f"\nDone. {len(existing)} repos in {OUTFILE}")


if __name__ == "__main__":
    main()
