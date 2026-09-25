#!/usr/bin/env python3
"""Build wolffcatskyy.dev.

Fills the {{...}} tokens in src/ with live numbers from the GitHub API and writes
the site to dist/. Standard library only. Any API failure stops the build, so a
bad fetch never ships wrong numbers; the last good deploy stays live.

Tokens:
  {{STARS:<repo>}}  stargazers_count of wolffcatskyy/<repo>
  {{TOTAL_STARS}}   sum of every {{STARS:...}} repo on the page
  {{PROJECT_COUNT}} number of distinct {{STARS:...}} repos on the page
  {{FEED_COUNT}}    len(BLOCKLIST_SOURCES) in crowdsec-blocklist-import's latest release

Set GITHUB_TOKEN to avoid the 60 requests/hour anonymous limit.
"""
import ast
import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

OWNER = "wolffcatskyy"
FEED_REPO = "crowdsec-blocklist-import"
FEED_FILE = "blocklist_import.py"
ROOT = Path(__file__).resolve().parent
SRC, PUBLIC, DIST = ROOT / "src", ROOT / "public", ROOT / "dist"
STAR_TOKEN = re.compile(r"\{\{STARS:([A-Za-z0-9._-]+)\}\}")


def get(url, accept="application/vnd.github+json"):
    headers = {"Accept": accept, "User-Agent": "wolffcatskyy.dev-build"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read()


def stars(repo):
    data = json.loads(get(f"https://api.github.com/repos/{OWNER}/{repo}"))
    return int(data["stargazers_count"])


def feed_count():
    tag = json.loads(get(f"https://api.github.com/repos/{OWNER}/{FEED_REPO}/releases/latest"))["tag_name"]
    source = get(
        f"https://api.github.com/repos/{OWNER}/{FEED_REPO}/contents/{FEED_FILE}?ref={tag}",
        accept="application/vnd.github.raw",
    ).decode()
    for node in ast.walk(ast.parse(source)):
        target = getattr(node, "target", None) or (node.targets[0] if isinstance(node, ast.Assign) else None)
        if isinstance(target, ast.Name) and target.id == "BLOCKLIST_SOURCES" and isinstance(node.value, ast.List):
            return len(node.value.elts), tag
    sys.exit(f"BLOCKLIST_SOURCES list not found in {FEED_REPO}@{tag}/{FEED_FILE}")


def main():
    templates = {p: p.read_text() for p in SRC.rglob("*") if p.is_file()}
    repos = sorted({m for text in templates.values() for m in STAR_TOKEN.findall(text)})
    counts = {repo: stars(repo) for repo in repos}
    feeds, tag = feed_count()
    values = {
        "TOTAL_STARS": f"{sum(counts.values()):,}",
        "PROJECT_COUNT": str(len(repos)),
        "FEED_COUNT": str(feeds),
    }

    if DIST.exists():
        shutil.rmtree(DIST)
    if PUBLIC.exists():
        shutil.copytree(PUBLIC, DIST)
    DIST.mkdir(exist_ok=True)

    for path, text in templates.items():
        text = STAR_TOKEN.sub(lambda m: f"{counts[m.group(1)]:,}", text)
        for key, value in values.items():
            text = text.replace("{{%s}}" % key, value)
        leftover = re.findall(r"\{\{[^}]*\}\}", text)
        if leftover:
            sys.exit(f"{path.name}: unknown tokens {sorted(set(leftover))}")
        out = DIST / path.relative_to(SRC)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)

    print(json.dumps({"stars": counts, **values, "feed_source": f"{FEED_REPO}@{tag}"}, indent=2))


if __name__ == "__main__":
    main()
