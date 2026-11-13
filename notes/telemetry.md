# Telemetry and evaluation tooling: review

Research pass on Nov 13, 2026, from each tool's official documentation (pages carry no
dates; re-check before adopting). "Unverified" means not confirmed on a page opened.

## What Claude Code already emits

- OpenTelemetry, off by default. `CLAUDE_CODE_ENABLE_TELEMETRY=1` plus an exporter per
  signal: metrics (tokens, cost), log events (prompt, API request, tool result, with cost
  and duration), and traces (beta; needs `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`).
  Content is opt-in: `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`,
  `OTEL_LOG_TOOL_CONTENT`. https://code.claude.com/docs/en/monitoring-usage
- Session transcripts as JSONL under `~/.claude/projects/`, kept 30 days by default; the
  format is internal and may change. https://code.claude.com/docs/en/sessions
- Hooks (`PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd`, `SubagentStop`) receive the
  session id, transcript path and tool input. https://code.claude.com/docs/en/hooks
- Headless runs: `claude -p --output-format json` returns the result, session id, usage
  and an estimated cost; `stream-json` gives every message. `--bare` skips hooks.
  https://code.claude.com/docs/en/headless

## Tools

| Tool | Claude Code path | Evals and datasets | Runs locally | Free tier | Licence |
|---|---|---|---|---|---|
| Langfuse | official plugin or a Stop hook; OTLP traces over HTTP | datasets, experiments, scores, LLM judge, annotation | Docker compose, several containers | cloud: 50k units a month, 30 days | MIT (except `/ee`) |
| LangSmith | official plugin; OTLP traces | datasets, experiments, evaluators | enterprise only | 1 seat, 5k traces a month, 14 days | proprietary (unverified) |
| Arize Phoenix | plugin built on hooks | included | one command | self-host free | Elastic License 2.0 |
| MLflow 3.4+ | `mlflow autolog claude` (writes hooks into settings) | unverified | SQLite + server | self-host free | unverified |
| Braintrust | Agent SDK only, no CLI path documented | unverified | unverified | unverified | unverified |

Sources: https://langfuse.com/integrations/other/claude-code ,
https://langfuse.com/pricing , https://docs.langchain.com/langsmith/trace-claude-code ,
https://www.langchain.com/pricing ,
https://arize.com/docs/phoenix/integrations/coding-agents/claude-code ,
https://mlflow.org/docs/latest/genai/tracing/integrations/listing/claude_code/

## Recommendation from the review

1. No service: run each skill headless with `--output-format stream-json`, save the
   stream to `runs/<run_id>.jsonl`, and write a small metadata file (provider, skill,
   git commit, session id). Risk: the stream format is internal and can change, so keep
   the raw files and parse later.
2. If a browsable UI is wanted: the Langfuse plugin against its free cloud tier. Risks:
   the hook fails silently when misconfigured, truncates long text, and the free tier
   keeps 30 days.
3. Later, for evals: load the 11 labelled items as a dataset and push scores (label
   agreement, schema validity, citation checks) from a local script.

Whatever the tool, the record stays in plain files in this repository: evidence ledgers,
candidates, scorecards, the human labels, computed scores keyed by run id, and the skill
versions in git. The tracing tool is a viewer.
