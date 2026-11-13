# Search providers

The skills use three capabilities and never name a tool directly. Every result goes
through `tools/ledger.py` into `evidence/<provider>/<candidate_id>.jsonl`; `/judge`
reasons only from the ledger.

| Capability | `claude` (built now) | `youcom` (Saturday) |
|---|---|---|
| `search(query, since, domains)` | WebSearch | You.com search tool |
| `fetch(url)` | WebFetch | You.com contents tool |
| `research(question)` | a subagent that searches and fetches | You.com research tool |

Outputs are kept apart per provider (`evidence/<provider>/`, `candidates/<provider>/`,
`scorecards/<provider>/`) so the two can be compared on the same inputs.

Rules for every provider:
- `linkedin.com` is never searched, fetched or cited. A LinkedIn URL may be stored as
  an identifier in `discovered_via` only.
- Store URLs and short paraphrases. Never store the text of someone else's post or page.
- Search window: `scan.window_days` in `spec.yaml` (120 days).
