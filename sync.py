#!/usr/bin/env python3
"""Sync the public Price per 1M dataset into this repository.

Pulls the machine-readable endpoints from https://www.priceper1m.com and writes
them under data/. Run by .github/workflows/sync.yml every 6 hours, and usable
locally:  python3 sync.py            (writes data/)
          python3 sync.py --check    (exit 1 if something would change)

The dataset itself is CC BY 4.0. Attribution: "Price per 1M (https://www.priceper1m.com)".
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://www.priceper1m.com"
ENDPOINTS = {
    "models.json": "/api/models",
    "changelog.json": "/api/changelog",
    "providers.json": "/api/providers",
}
UA = "priceper1m-dataset-mirror/1.0 (+https://www.priceper1m.com)"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STAMP = ROOT / "LAST_SYNC.txt"


def fetch(path: str, attempts: int = 3) -> dict:
    last: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(BASE + path, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                if r.status != 200:
                    raise RuntimeError(f"{path} -> HTTP {r.status}")
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise  # endpoint not deployed yet — do not retry, caller decides
            last = exc
        except Exception as exc:  # noqa: BLE001 — transient network/CDN issues
            last = exc
        if i < attempts - 1:
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{path}: {last}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if the mirror is stale")
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    changed: list[str] = []
    skipped: list[str] = []
    summary: dict[str, object] = {}

    for name, endpoint in ENDPOINTS.items():
        try:
            payload = fetch(endpoint)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                # Endpoint not deployed yet (or retired). Keep whatever we already
                # have in the mirror and let the next run pick it up.
                print(f"~~ {endpoint}: HTTP 404 — endpoint not live yet, keeping existing {name}", file=sys.stderr)
                skipped.append(name)
                continue
            print(f"!! {endpoint}: HTTP {exc.code}", file=sys.stderr)
            return 2
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"!! {endpoint}: {exc}", file=sys.stderr)
            return 2

        text = json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
        target = DATA / name
        previous = target.read_text(encoding="utf-8") if target.exists() else None
        if previous != text:
            changed.append(name)
            if not args.check:
                target.write_text(text, encoding="utf-8")

        if name == "models.json":
            summary["models"] = payload.get("count")
            summary["generated_at"] = payload.get("generated_at")
        elif name == "changelog.json":
            summary["runs"] = payload.get("count_runs")
            summary["changes"] = payload.get("count_changes")
        elif name == "providers.json":
            summary["providers"] = payload.get("count")

    stamp = (
        f"last sync: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"models: {summary.get('models')}\n"
        f"providers: {summary.get('providers')}\n"
        f"changelog runs: {summary.get('runs')} ({summary.get('changes')} diffs)\n"
        f"source generated_at: {summary.get('generated_at')}\n"
    )
    if not args.check:
        # Only touch the stamp when the data really moved (or on the very first run).
        # The stamp carries the current time, so rewriting it unconditionally would make
        # every scheduled run look like a change and commit nothing but noise.
        if changed or not STAMP.exists():
            STAMP.write_text(stamp, encoding="utf-8")

    print(stamp.strip())
    print("changed files:", ", ".join(changed) if changed else "(none)")

    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
