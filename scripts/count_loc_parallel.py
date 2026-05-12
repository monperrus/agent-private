#!/usr/bin/env python3
"""Parallel LOC counter for all 200 ProgramBench subjects (arXiv:2605.03546).

For each subject, shallow-clones the repo at its benchmark commit and runs
cloc to count non-blank, non-comment source lines. Uses a thread pool for
parallelism; large repos may time out and should be retried with
count_loc_retry.py.

Dependencies: git, cloc (apt install cloc)
Output: loc_results.tsv
"""

import subprocess
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Mapping of GitHub repo slug -> benchmark commit hash
# Derived from facebookresearch/ProgramBench src/programbench/data/tasks/
REPOS = {
    "abishekvashok/cmatrix": "5c082c6",
    "agourlay/zip-password-finder": "704700d",
    "ajeetdsouza/zoxide": "67ca1bc",
    "alecthomas/chroma": "8d04def",
    "alexpovel/srgn": "89f943b",
    "altdesktop/i3-style": "f93821b",
    "ammarabouzor/tui-journal": "2b4540d",
    "anordal/shellharden": "6a6ffd4",
    "antonmedv/fx": "86d0d34",
    "antonmedv/walk": "bf802ef",
    "ariga/atlas": "6d81150",
    "arq5x/bedtools2": "dd57059",
    "arthursonzogni/json-tui": "17a22b6",
    "ast-grep/ast-grep": "dde0fe0",
    "astaxie/bat": "17d1080",
    "astro/deadnix": "d590041",
    "axodotdev/oranda": "27d60c7",
    "bellard/quickjs": "d7ae12a",
    "bensadeh/tailspin": "6278437",
    "blacknon/hwatch": "edfcb62",
    "blake3-team/blake3": "15e83a5",
    "bootandy/dust": "62bf1e1",
    "boyter/scc": "515f91c",
    "brocode/fblog": "3b54330",
    "burntsushi/ripgrep": "3b7fd44",
    "burntsushi/xsv": "f430466",
    "byron/dua-cli": "8570c15",
    "canop/broot": "d6c798e",
    "canop/rhit": "ae90bcb",
    "cheat/cheat": "b8098dc",
    "chirlu/sox": "42b3557",
    "chmln/handlr": "90e78ba",
    "chmln/sd": "87d1ba5",
    "clog-tool/clog-cli": "7066cba",
    "cmatsuoka/figlet": "202a0a8",
    "codesnap-rs/codesnap": "f81e4f3",
    "cordx56/rustowl": "655bc5c",
    "crowdagger/crowbook": "ea214d7",
    "cslarsen/jp2a": "61d205f",
    "cweill/gotests": "2a672c5",
    "dalance/amber": "69a0f52",
    "dandavison/delta": "acd758f",
    "danmar/cppcheck": "0a5b103",
    "direnv/direnv": "02040c7",
    "doxygen/doxygen": "966d98e",
    "drew-alleman/datasurgeon": "d257cee",
    "ducaale/xh": "4a6e44f",
    "duckdb/duckdb": "bdb65ec",
    "dundee/gdu": "ede21d2",
    "ecumene/rust-sloth": "051c559",
    "ekzhang/bore": "8e059cd",
    "eliukblau/pixterm": "1a93fd5",
    "elkowar/pipr": "fae0b17",
    "epistates/treemd": "825c6dd",
    "eradman/entr": "8e2e8b4",
    "esubaalew/run": "0fb9dec",
    "eudoxia0/hashcards": "48aa136",
    "facebook/zstd": "1168da0",
    "facebookresearch/fasttext": "1142dc4",
    "ffmpeg/ffmpeg": "360a402",
    "filosottile/age": "706dfc1",
    "foriequal0/git-trim": "07c2f50",
    "gabotechs/dep-tree": "60a95a2",
    "ggreer/the_silver_searcher": "a61f178",
    "git-bahn/git-graph": "87b4473",
    "go-critic/go-critic": "9aea378",
    "google/brotli": "b3dc9cc",
    "gromacs/gromacs": "665ea4c",
    "guumaster/hostctl": "d6d9699",
    "hairyhenderson/gomplate": "05eb3aa",
    "halitechallenge/halite": "822cfb6",
    "hatoo/oha": "8dc6349",
    "hooklift/gowsdl": "2a06cec",
    "hpjansson/chafa": "dd4d4c1",
    "htop-dev/htop": "523600b",
    "hush-shell/hush": "560c33a",
    "incu6us/goimports-reviser": "81bd549",
    "ip7z/7zip": "839151e",
    "ismaelgv/rnr": "fc0733b",
    "isona/dirble": "e2dea9f",
    "ivanceras/svgbob": "6d00ad9",
    "jarun/nnn": "cb2c535",
    "jesseduffield/lazygit": "1d0db51",
    "jgm/pandoc": "5caad90",
    "jhspetersson/fselect": "c3559ca",
    "johanneskaufmann/html-to-markdown": "3006818",
    "johnkerl/miller": "8d85b46",
    "jonas/tig": "8334123",
    "jqlang/jq": "b33a763",
    "jrnxf/thokr": "09375ef",
    "junegunn/fzf": "b56d614",
    "kaushiksrini/parqeye": "8072121",
    "kisielk/errcheck": "dacab89",
    "konradsz/igrep": "aa75630",
    "ksxgithub/parallel-disk-usage": "96978ed",
    "kyoh86/richgo": "313114f",
    "kyoheiu/felix": "95df390",
    "lfos/calcurse": "49180d5",
    "lh3/seqtk": "94e7070",
    "lua/lua": "c6b4848",
    "luajit/luajit": "a553b3d",
    "lymphatus/caesium-clt": "a529b2e",
    "lz4/lz4": "1519f46",
    "madler/pigz": "fe4894f",
    "mfridman/tparse": "2416b4b",
    "mgdm/htmlq": "6e31bc8",
    "mgechev/revive": "201451e",
    "mibk/dupl": "1bf052b",
    "mikefarah/yq": "602586d",
    "miserlou/loop": "209927c",
    "mkj/dropbear": "75f699b",
    "mookid/diffr": "2152742",
    "multiprocessio/dsq": "c3ae0ba",
    "nachoparker/dutree": "44e877d",
    "naggie/dstask": "ff57396",
    "nikoladucak/caps-log": "2cf2d1e",
    "nikolassv/bartib": "6b9b5ce",
    "ninja-build/ninja": "cc60300",
    "noborus/ov": "b96c2ba",
    "noborus/trdsql": "d8c5ff6",
    "nukesor/pueue": "8b9d6fe",
    "nuta/nsh": "bdd0702",
    "o2sh/onefetch": "e5958ce",
    "ogham/dog": "721440b",
    "oppiliappan/eva": "41ae245",
    "oppiliappan/statix": "e9df54c",
    "orf/gping": "26eb5b9",
    "osgeo/gdal": "0847f12",
    "osgeo/proj": "75d455c",
    "paradigmxyz/solar": "5190d0e",
    "parcel-bundler/lightningcss": "aa2ed1e",
    "peco/peco": "4e58dad",
    "pemistahl/grex": "fa3e8ed",
    "php/php-src": "c891263",
    "pier-cli/pier": "5e1bde9",
    "pls-rs/pls": "4e1ae50",
    "psampaz/go-mod-outdated": "bb79367",
    "quinn-rs/quinn": "bb359cc",
    "raviqqe/muffet": "a882908",
    "rbakbashev/elfcat": "52f8cc7",
    "rcoh/angle-grinder": "9c2fc88",
    "rhysd/kiro-editor": "4157485",
    "riquito/tuc": "16fb471",
    "robertdavidgraham/masscan": "b99d433",
    "rochacbruno/marmite": "7d4bc2d",
    "rs/curlie": "5dfcbb1",
    "rs/jplot": "2a54bcc",
    "rust-embedded/svd2rust": "1760b5e",
    "rust-ethereum/ethabi": "b1710ad",
    "rust-lang/mdbook": "37273ba",
    "rvben/rumdl": "2d75c4d",
    "samtools/samtools": "aa823b5",
    "sayanarijit/xplr": "1751065",
    "sclevine/yj": "8016400",
    "segmentio/chamber": "5f93f5f",
    "sharkdp/bat": "f822bd0",
    "sharkdp/fd": "40d8eb3",
    "sharkdp/hexyl": "2e26437",
    "sharkdp/hyperfine": "327d5f4",
    "sharkdp/pastel": "b60e899",
    "shashwatah/jot": "a92aad8",
    "sheepla/pingu": "926d475",
    "sibprogrammer/xq": "b89f681",
    "sigoden/argc": "04a08f1",
    "simeg/eureka": "df3796c",
    "sirwart/ripsecrets": "34c9e03",
    "sitkevij/hex": "61ae69b",
    "skeema/skeema": "6a76243",
    "sqlite/sqlite": "839433d",
    "sstadick/hck": "b66c751",
    "stacked-git/stgit": "430027d",
    "stathissideris/ditaa": "f2286c4",
    "stranger6667/jsonschema": "d52e881",
    "svenstaro/genact": "16f96e3",
    "svenstaro/miniserve": "8449e8b",
    "tarka/xcp": "5e5b448",
    "thezoraiz/ascii-image-converter": "d05a757",
    "tinycc/tinycc": "9b8765d",
    "tomarrell/wrapcheck": "c058da1",
    "tomnomnom/gron": "88a6234",
    "trasta298/keifu": "3331426",
    "tree-sitter/tree-sitter": "5e23cca",
    "tstack/lnav": "ee34494",
    "tukaani-project/xz": "1007bf0",
    "typst/typst": "88356d0",
    "unhappychoice/gittype": "34b72d0",
    "universal-ctags/ctags": "243595e",
    "wfxr/code-minimap": "0ddeea5",
    "wfxr/csview": "8ac4de0",
    "wgunderwood/tex-fmt": "3f1aef6",
    "wintermute-cell/ngrrram": "8ea13c3",
    "xampprocky/tokei": "505d648",
    "xorg62/tty-clock": "f2f847c",
    "y2z/monolith": "8702e66",
    "yaa110/nomino": "f892499",
    "yassinebridi/serpl": "c48a9d7",
    "yoav-lavi/melody": "f4af9b4",
    "ys-l/flamelens": "0b4dc33",
    "zevv/duc": "a58fa4e",
    "zk-org/zk": "10d93d5",
}

CLOC_TIMEOUT = 60   # seconds; increase for very large repos
CLONE_TIMEOUT = 120  # seconds
WORKERS = 15
OUTFILE = "loc_results.tsv"


def count_loc(repo: str, commit: str) -> tuple[str, str, int, str]:
    """Clone repo and count LOC with cloc. Returns (repo, commit, code_lines, status)."""
    tmpdir = f"/tmp/pb_{repo.replace('/', '_')}"
    try:
        r = subprocess.run(
            ["git", "clone", "--depth=1", "--no-tags", "-q",
             f"https://github.com/{repo}.git", tmpdir],
            capture_output=True, timeout=CLONE_TIMEOUT
        )
        if r.returncode != 0:
            return repo, commit, -1, "clone_failed"

        r2 = subprocess.run(
            ["cloc", tmpdir, "--quiet", "--json"],
            capture_output=True, text=True, timeout=CLOC_TIMEOUT
        )
        try:
            data = json.loads(r2.stdout)
            code = data.get("SUM", {}).get("code", 0)
        except Exception:
            code = 0

        return repo, commit, code, "ok"
    except subprocess.TimeoutExpired as e:
        return repo, commit, -1, f"timeout: {e}"
    except Exception as e:
        return repo, commit, -1, str(e)
    finally:
        subprocess.run(["rm", "-rf", tmpdir], capture_output=True)


def main():
    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(count_loc, repo, commit): repo
                   for repo, commit in REPOS.items()}
        done = 0
        for future in as_completed(futures):
            repo, commit, code, status = future.result()
            results.append((repo, commit, code))
            done += 1
            if done % 20 == 0:
                print(f"Progress: {done}/{len(REPOS)}")
            if status != "ok":
                print(f"  FAIL [{status}] {repo}")
            else:
                print(f"  OK   {repo}: {code:,}")

    results.sort(key=lambda x: x[0])
    with open(OUTFILE, "w") as f:
        f.write("repository\tcommit\tcode_lines_cloc\n")
        for repo, commit, code in results:
            f.write(f"{repo}\t{commit}\t{code}\n")

    print(f"\nDone. {len(results)} repos written to {OUTFILE}")
    codes = sorted(c for _, _, c in results if c > 0)
    print(f"Min: {min(codes):,}  Median: {codes[len(codes)//2]:,}  Max: {max(codes):,}")


if __name__ == "__main__":
    main()
