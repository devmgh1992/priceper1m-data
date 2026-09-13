# AI model API pricing dataset — live mirror

Machine-readable snapshot of **[Price per 1M](https://www.priceper1m.com)** — per-1M-token prices for every AI/LLM model we can price, refreshed **every 6 hours** by a GitHub Action that pulls the public endpoints and commits only when the data actually changed.

```
data/models.json       all tracked endpoints: input / output / cached prices, context window, capabilities
data/changelog.json    every detected price movement, as a diff log (changed / added / removed)
data/providers.json    per-provider rollup: model count + input-price floor
LAST_SYNC.txt          freshness stamp (source generated_at, counts)
```

| | |
|---|---|
| **Models priced** | chat models with a published input *and* output rate, plus embeddings |
| **Providers** | every provider in the upstream registries we aggregate |
| **Unit** | USD per 1,000,000 tokens (list prices, no discounts) |
| **Freshness** | rebuilt every 6 hours; `generated_at` in each file is authoritative |
| **License** | data CC BY 4.0 — attribution: *Price per 1M, https://www.priceper1m.com* |
| **Code** | MIT |

## Quick start

```bash
# no dependencies beyond the standard library
python3 sync.py            # refresh data/ in place
python3 sync.py --check    # exit 1 if the mirror is stale (useful in CI)
```

```python
import json

models = json.load(open("data/models.json"))["models"]
chat = [m for m in models if m["kind"] == "chat" and m["input_per_1m"] is not None]

for m in sorted(chat, key=lambda m: m["input_per_1m"])[:10]:
    print(f'{m["name"]:<28} {m["provider"]:<16} ${m["input_per_1m"]:>7}/1M in')
```

## Live endpoints (same data, always current)

| Endpoint | What it returns |
|---|---|
| `https://www.priceper1m.com/api/models` | full dataset |
| `https://www.priceper1m.com/api/model/{slug}` | one model |
| `https://www.priceper1m.com/api/changelog` | price-change diff log |
| `https://www.priceper1m.com/api/providers` | provider rollups |
| `https://www.priceper1m.com/llms.txt` | agent-oriented map of the site |
| `https://www.priceper1m.com/digest` | weekly price reports (one per ISO week) |

## How the numbers are produced

1. **Collect** — public price registries and provider metadata are fetched on a schedule.
2. **Normalise** — every model is mapped to one schema: `input_per_1m`, `output_per_1m`, `cached_input_per_1m`, `context_window`, `max_output`, capability flags. Missing prices stay `null` rather than being guessed.
3. **Diff** — each run diffs against the previous snapshot, so `data/changelog.json` records exactly what moved, with the before/after values and percentage.
4. **Publish** — the dataset ships to the site, to this mirror, and to the free API in the same run.

Where two independent sources cover the same model, the site's model pages show both so disagreements stay visible. Method and caveats: <https://www.priceper1m.com/methodology>.

## Notes and caveats

- These are **published list prices**. They ignore regional multipliers, committed-use discounts, batch tiers and free allowances — use them to compare models like-for-like, then confirm budgets with the provider.
- Prices change without notice. Always check `generated_at` (and the model's `price_checked_at`) before quoting a figure.
- A model with `null` prices was found in a catalogue but could not be priced from a public source; it is not a $0 model.
- Corrections are welcome — open an issue with the source URL and the affected slug.

## Attribution

If you publish anything built on this data, link back to <https://www.priceper1m.com> (CC BY 4.0 requires attribution; the link is what keeps the pipeline funded).
