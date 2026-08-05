#!/usr/bin/env python3
"""Regenerate the featured / currently-building sections of the profile README.

Picks the top 4 non-fork repos by last push (excluding the profile repo
itself), plus the single most recently pushed repo for the "Currently
building" line. Commits and pushes only when the README actually changed.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request

USER = "davidsilva131"
API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN", "")
README = "README.md"
TOP_N = 4


def api(path: str):
    req = urllib.request.Request(f"{API}{path}")
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-readme-updater")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def entry(repo: dict) -> str:
    desc = (repo.get("description") or "").strip()
    lang = repo.get("language")
    line = f"- **[{repo['name']}]({repo['html_url']})**"
    if desc:
        line += f" — {desc}"
    if lang:
        line += f" · {lang}"
    return line


def main() -> int:
    repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed")
    mine = [
        r for r in repos
        if not r["fork"] and r["name"] != USER and not r.get("archived")
    ]
    mine.sort(key=lambda r: r["pushed_at"], reverse=True)

    top = mine[:TOP_N]
    current = mine[0] if mine else None

    featured = "\n".join(entry(r) for r in top)
    now = entry(current) if current else "_Nothing yet_"

    with open(README, encoding="utf-8") as fh:
        original = fh.read()

    updated = re.sub(
        r"<!--FEATURED:START-->.*?<!--FEATURED:END-->",
        f"<!--FEATURED:START-->\n{featured}\n<!--FEATURED:END-->",
        original,
        flags=re.DOTALL,
    )
    updated = re.sub(
        r"<!--NOW:START-->.*?<!--NOW:END-->",
        f"<!--NOW:START-->\n{now}\n<!--NOW:END-->",
        updated,
        flags=re.DOTALL,
    )

    if updated == original:
        print("README unchanged — nothing to commit")
        return 0

    with open(README, "w", encoding="utf-8") as fh:
        fh.write(updated)

    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    subprocess.run(["git", "add", README], check=True)
    subprocess.run(["git", "commit", "-m", "chore: update featured repos [skip ci]"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("README updated and pushed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
