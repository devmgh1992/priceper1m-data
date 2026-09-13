#!/usr/bin/env python3
"""Ten cheapest chat models right now, straight from the mirror.

    python3 examples/cheapest_models.py

Reads data/models.json if you have cloned the repo, otherwise falls back to the
live API. Handy as a starting point for your own cost dashboards.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = "https://www.priceper1m.com/api/models"


def load() -> dict:
    local = ROOT / "data" / "models.json"
    if local.exists():
        return json.loads(local.read_text(encoding="utf-8"))
    req = urllib.request.Request(LIVE, headers={"User-Agent": "priceper1m-example/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def money(v: float | None) -> str:
    return "—" if v is None else f"${v:g}"


def main() -> None:
    doc = load()
    print(f"dataset generated_at: {doc['generated_at']}  ({doc['count']} endpoints)\n")

    priced = [
        m
        for m in doc["models"]
        if m["kind"] == "chat" and m["input_per_1m"] is not None and m["output_per_1m"] is not None
    ]
    free = [m for m in priced if m["input_per_1m"] == 0]
    paid = [m for m in priced if m["input_per_1m"] > 0]
    cheapest = sorted(paid, key=lambda m: m["input_per_1m"])[:10]

    print(f"{len(priced)} priceable chat models · {len(free)} at $0 list price · cheapest 10 paid:\n")
    print(f"{'model':<32}{'provider':<18}{'in $/1M':>9}{'out $/1M':>10}{'context':>10}")
    print("-" * 79)
    for m in cheapest:
        ctx = m.get("context_window") or 0
        print(
            f"{m['name'][:31]:<32}{m['provider'][:17]:<18}"
            f"{money(m['input_per_1m']):>9}{money(m['output_per_1m']):>10}"
            f"{ctx / 1000:>9.0f}K"
        )

    # a support bot doing 10k chats/day: 1.2k tokens in, 400 out
    top = cheapest[0]
    monthly = (((1200 * top["input_per_1m"]) + (400 * top["output_per_1m"])) / 1_000_000) * 10_000 * 30
    print(f"\n{top['name']} at 10,000 chats/day for a month: ${monthly:,.2f}")
    print("\nAttribution: Price per 1M — https://www.priceper1m.com (CC BY 4.0)")


if __name__ == "__main__":
    main()
