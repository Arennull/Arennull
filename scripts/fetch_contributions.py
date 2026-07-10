#!/usr/bin/env python3
"""
fetch_contributions.py — scrape a GitHub contribution calendar with NO auth.

Reads the public HTML fragment at github.com/users/<user>/contributions
(no token, no API key), parses the day grid + per-day tooltips, computes streak
stats, and writes contributions.json for render_heatmap_svg.py.

Usage:
    GH_PROFILE_USER=Arennull python scripts/fetch_contributions.py [contributions.json]

Deps (lightweight, CI-friendly):  pip install -r scripts/requirements.txt
"""
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone

import requests
from bs4 import BeautifulSoup

# ============================= CONFIG (edit me) =============================
DEFAULT_USER = "Arennull"
ENDPOINT     = "https://github.com/users/{user}/contributions"
USER_AGENT   = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")
TIMEOUT      = 20
RETRIES      = 3
# When a tooltip is missing, approximate the count from the level bucket.
LEVEL_TO_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}
# ===========================================================================

USER = os.environ.get("GH_PROFILE_USER", DEFAULT_USER)


def fetch_html(user: str) -> str:
    url = ENDPOINT.format(user=user)
    headers = {
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html",
    }
    last = None
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 ** attempt)
    raise SystemExit(f"failed to fetch contributions for {user}: {last}")


def parse(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # id -> exact count, from the <tool-tip> custom elements at the end
    id_to_count = {}
    for tip in soup.find_all("tool-tip"):
        key = tip.get("for")
        if not key:
            continue
        text = tip.get_text(strip=True)
        m = re.match(r"^(No|[\d,]+)", text)
        if not m:
            continue
        token = m.group(1)
        id_to_count[key] = 0 if token == "No" else int(token.replace(",", ""))

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        d = td.get("data-date")
        if not d:
            continue
        level = int(td.get("data-level", 0) or 0)
        cid = td.get("id")
        count = id_to_count.get(cid)
        if count is None:
            # older markup exposed data-count directly; else fall back to level
            dc = td.get("data-count")
            count = int(dc) if dc is not None else LEVEL_TO_COUNT.get(level, 0)
        days.append({"date": d, "count": int(count), "level": level})

    # dedupe + sort ascending
    seen = {}
    for row in days:
        seen[row["date"]] = row
    return [seen[k] for k in sorted(seen)]


def streaks(days):
    total = sum(d["count"] for d in days)
    max_day = max((d["count"] for d in days), default=0)

    # longest run of active days
    longest = cur = 0
    longest_start = longest_end = cur_start = None
    for d in days:
        if d["count"] > 0:
            cur += 1
            if cur == 1:
                cur_start = d["date"]
            if cur > longest:
                longest, longest_start, longest_end = cur, cur_start, d["date"]
        else:
            cur = 0

    # current streak: count back from today, tolerating "today not done yet"
    today = datetime.now(timezone.utc).date()
    by_date = {d["date"]: d for d in days}
    cursor = today
    if by_date.get(cursor.isoformat(), {}).get("count", 0) == 0:
        cursor = date.fromordinal(today.toordinal() - 1)  # start from yesterday
    length = 0
    cur_start_d = cur_end_d = None
    while True:
        key = cursor.isoformat()
        row = by_date.get(key)
        if not row or row["count"] == 0:
            break
        if cur_end_d is None:
            cur_end_d = key
        cur_start_d = key
        length += 1
        cursor = date.fromordinal(cursor.toordinal() - 1)

    return {
        "total": total,
        "max_day": max_day,
        "current_streak": {"length": length, "start": cur_start_d, "end": cur_end_d},
        "longest_streak": {"length": longest, "start": longest_start, "end": longest_end},
    }


def main() -> None:
    dst = sys.argv[1] if len(sys.argv) > 1 else "contributions.json"
    html = fetch_html(USER)
    days = parse(html)
    if not days:
        print("[contrib] WARNING: parsed 0 days — writing zeroed file.")
    stats = streaks(days)
    payload = {
        "user": USER,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **stats,
        "days": days,
    }
    with open(dst, "w") as fh:
        json.dump(payload, fh, indent=1)
    cs = stats["current_streak"]["length"]
    ls = stats["longest_streak"]["length"]
    print(f"[contrib] {USER}: {len(days)} days, total={stats['total']}, "
          f"current={cs}, longest={ls} -> {dst}")


if __name__ == "__main__":
    main()
