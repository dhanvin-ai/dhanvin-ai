#!/usr/bin/env python3
"""Generate profile cards from the owner's public GitHub repositories."""

import html
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "dhanvin-ai")
OUTPUT = Path(os.environ.get("PROFILE_ASSETS_DIR", "dist"))
TOKEN = os.environ.get("GITHUB_TOKEN", "")
COLORS = ["#7aa2f7", "#2ac3de", "#bb9af7", "#e0af68", "#9ece6a", "#f7768e"]


def api(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "dhanvin-ai-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def svg(title, body, width=495, height=195):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">
  <title>{html.escape(title)}</title>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="10" fill="#1a1b27" stroke="#414868" stroke-width="2"/>
  <text x="24" y="43" fill="#7aa2f7" font-family="Arial, Helvetica, sans-serif" font-size="24" font-weight="700">{html.escape(title)}</text>
  {body}
</svg>
'''


def stat_card(user, repositories):
    stats = [
        ("Public repositories", len(repositories)),
        ("Stars earned", sum(repo["stargazers_count"] for repo in repositories)),
        ("Forks", sum(repo["forks_count"] for repo in repositories)),
        ("Followers", user["followers"]),
    ]
    parts = []
    for index, (label, value) in enumerate(stats):
        x = 28 + (index % 2) * 240
        y = 91 + (index // 2) * 64
        parts.append(
            f'<text x="{x}" y="{y}" fill="#a9b1d6" font-family="Arial, Helvetica, sans-serif" font-size="15">{html.escape(label)}</text>'
            f'<text x="{x}" y="{y+32}" fill="#c0caf5" font-family="Arial, Helvetica, sans-serif" font-size="27" font-weight="700">{value:,}</text>'
        )
    return svg(f"{OWNER}'s GitHub statistics", "\n  ".join(parts))


def languages_card(repositories):
    totals = {}
    for repo in repositories:
        if repo["fork"]:
            continue
        languages = api(f'/repos/{quote(OWNER)}/{quote(repo["name"])}/languages')
        for name, size in languages.items():
            totals[name] = totals.get(name, 0) + size

    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:6]
    total = sum(totals.values()) or 1
    parts = ['<rect x="24" y="62" width="447" height="13" rx="6" fill="#292e42"/>']
    cursor = 24.0
    for index, (name, size) in enumerate(top):
        width = 447 * size / total
        parts.append(f'<rect x="{cursor:.2f}" y="62" width="{width:.2f}" height="13" fill="{COLORS[index]}"/>')
        cursor += width
        x = 24 + (index % 2) * 232
        y = 104 + (index // 2) * 29
        label = html.escape(f"{name} {size / total:.1%}")
        parts.append(f'<circle cx="{x+6}" cy="{y-5}" r="6" fill="{COLORS[index]}"/>')
        parts.append(f'<text x="{x+19}" y="{y}" fill="#c0caf5" font-family="Arial, Helvetica, sans-serif" font-size="14">{label}</text>')
    if not top:
        parts.append('<text x="24" y="112" fill="#c0caf5" font-family="Arial, Helvetica, sans-serif" font-size="15">No public repository languages yet</text>')
    return svg("Most Used Languages", "\n  ".join(parts))


def main():
    user = api(f"/users/{quote(OWNER)}")
    repositories = []
    page = 1
    while True:
        batch = api(f"/users/{quote(OWNER)}/repos?type=owner&per_page=100&page={page}")
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "github-stats.svg").write_text(stat_card(user, repositories), encoding="utf-8")
    (OUTPUT / "top-languages.svg").write_text(languages_card(repositories), encoding="utf-8")


if __name__ == "__main__":
    main()
