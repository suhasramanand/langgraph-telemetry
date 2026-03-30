# Metrics catalog

All series use bounded labels. **Never** put prompts, run IDs, or raw graph state into labels.

## Names

| Metric | Type | Labels | Purpose |
| ------ | ---- | ------ | ------- |
| `langgraph_node_duration_seconds` | Histogram | `graph`, `node`, `namespace` | Time between `updates` (or task duration when `tasks` is in `stream_mode`) |
| `langgraph_graph_runs_total` | Counter | `graph`, `status` (`success` / `error`) | Stream wrapper completed once per run |
| `langgraph_stream_updates_total` | Counter | `graph` | Count of `type=updates` chunks |
| `langgraph_llm_tokens_total` | Counter | `graph`, `token_type` (`prompt` / `completion` / `total`) | From `on_llm_end` token usage when present |
| `langgraph_llm_calls_total` | Counter | `graph` | `on_llm_end` invocations |
| `langgraph_llm_usage_missing_total` | Counter | `graph` | LLM ended without parseable usage |
| `langgraph_errors_total` | Counter | `graph`, `error_class` | Stream or task failures observed |

## Cardinality

- `node` is sanitized (short alphanumeric + underscore). Unknown / invalid values collapse to `other`.
- `namespace` is derived from the LangGraph stream `ns` tuple via a depth-limited fingerprint, not the raw path.

## PromQL notes

- `histogram_quantile` needs sufficient samples. After deploy or restarts, wait for scrape intervals to accumulate.
- Prefer `rate(...[5m])` or `irate` depending on your scrape alignment.

## PII

Do not attach user identifiers, API keys, or message bodies to metrics or labels.
