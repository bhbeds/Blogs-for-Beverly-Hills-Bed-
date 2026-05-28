#!/usr/bin/env python3
"""
Ahrefs API v3 - SEO research tool for Beverly Hills Bed & Breakfast blogs.
Usage: python ahrefs_seo.py <command> [options]

Set AHREFS_API_KEY environment variable before running.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://api.ahrefs.com/v3"


def get_headers():
    key = os.environ.get("AHREFS_API_KEY")
    if not key:
        print("Error: AHREFS_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }


def request(endpoint, params=None):
    url = f"{API_BASE}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=get_headers())
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def keyword_overview(keyword, country="us"):
    """Get search volume, difficulty, and CPC for a keyword."""
    data = request("keywords-explorer/overview", {
        "select": "keyword,volume,difficulty,cpc,clicks,country",
        "country": country,
        "keywords": keyword,
    })
    return data


def keyword_ideas(keyword, country="us", limit=20):
    """Get related keyword ideas and questions."""
    data = request("keywords-explorer/matching-terms", {
        "select": "keyword,volume,difficulty,cpc",
        "country": country,
        "term": keyword,
        "limit": limit,
    })
    return data


def serp_overview(keyword, country="us"):
    """Get top-ranking pages for a keyword."""
    data = request("keywords-explorer/serp-overview", {
        "select": "url,title,ahrefs_rank,domain_rating,backlinks,traffic",
        "country": country,
        "keyword": keyword,
    })
    return data


def site_keywords(target, country="us", limit=20):
    """Get top organic keywords for a domain."""
    data = request("site-explorer/organic-keywords", {
        "select": "keyword,volume,difficulty,traffic,position,url",
        "target": target,
        "country": country,
        "limit": limit,
        "mode": "domain",
    })
    return data


def backlinks_overview(target):
    """Get backlink summary for a domain or URL."""
    data = request("site-explorer/backlinks-stats", {
        "target": target,
        "mode": "domain",
    })
    return data


def content_gap(target, competitors, country="us", limit=20):
    """Find keywords competitors rank for that target does not."""
    params = {
        "select": "keyword,volume,difficulty,best_position",
        "target": target,
        "country": country,
        "limit": limit,
        "mode": "domain",
    }
    for i, comp in enumerate(competitors):
        params[f"competitors[{i}]"] = comp
    return request("site-explorer/content-gap", params)


def print_table(rows, headers):
    if not rows:
        print("No results.")
        return
    widths = [max(len(str(r.get(h, ""))) for r in rows + [{}]) for h in headers]
    widths = [max(w, len(h)) for w, h in zip(widths, headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*[str(row.get(h, "")) for h in headers]))


def main():
    parser = argparse.ArgumentParser(description="Ahrefs SEO research CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("keyword", help="Overview for a keyword")
    p.add_argument("keyword")
    p.add_argument("--country", default="us")

    p = sub.add_parser("ideas", help="Keyword ideas / matching terms")
    p.add_argument("keyword")
    p.add_argument("--country", default="us")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("serp", help="SERP overview for a keyword")
    p.add_argument("keyword")
    p.add_argument("--country", default="us")

    p = sub.add_parser("site-keywords", help="Top organic keywords for a domain")
    p.add_argument("domain")
    p.add_argument("--country", default="us")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("backlinks", help="Backlink overview for a domain")
    p.add_argument("domain")

    p = sub.add_parser("content-gap", help="Content gap vs competitors")
    p.add_argument("domain")
    p.add_argument("competitors", nargs="+")
    p.add_argument("--country", default="us")
    p.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "keyword":
        data = keyword_overview(args.keyword, args.country)
        rows = data.get("keywords", [data.get("data", {})])
        print_table(rows, ["keyword", "volume", "difficulty", "cpc", "clicks"])

    elif args.cmd == "ideas":
        data = keyword_ideas(args.keyword, args.country, args.limit)
        rows = data.get("keywords", [])
        print_table(rows, ["keyword", "volume", "difficulty", "cpc"])

    elif args.cmd == "serp":
        data = serp_overview(args.keyword, args.country)
        rows = data.get("positions", [])
        print_table(rows, ["url", "title", "domain_rating", "backlinks", "traffic"])

    elif args.cmd == "site-keywords":
        data = site_keywords(args.domain, args.country, args.limit)
        rows = data.get("keywords", [])
        print_table(rows, ["keyword", "volume", "difficulty", "position", "traffic", "url"])

    elif args.cmd == "backlinks":
        data = backlinks_overview(args.domain)
        stats = data.get("stats", data)
        for k, v in stats.items():
            print(f"{k}: {v}")

    elif args.cmd == "content-gap":
        data = content_gap(args.domain, args.competitors, args.country, args.limit)
        rows = data.get("keywords", [])
        print_table(rows, ["keyword", "volume", "difficulty", "best_position"])


if __name__ == "__main__":
    main()
