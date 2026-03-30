# Groq chat agent (free tier) + Prometheus metrics

Same telemetry as the synthetic `basic_agent`, but calls **Groq’s** OpenAI-compatible chat API via `ChatGroq`, so you get real LLM traffic and token metrics.

## Setup

```bash
pip install -e ../../packages/langgraph-telemetry
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...   # from https://console.groq.com/
python main.py
```

Stop anything else using port **9100** before starting.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `GROQ_API_KEY` | (required) | Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Model id (see Groq docs) |
| `METRICS_PORT` | `9100` | `/metrics` port |
| `AGENT_SLEEP_SEC` | `4` | Seconds between turns |

## Live traffic (dashboard demos)

For denser Prometheus / chart activity, run several workers in one process (same `:9100` metrics):

```bash
export GROQ_API_KEY=gsk_...
python live_traffic.py
```

| Variable | Default | Meaning |
|----------|---------|---------|
| `LIVE_TRAFFIC_WORKERS` | `2` | Concurrent graph loops |
| `LIVE_TRAFFIC_SLEEP_SEC` | `4` | Pause between turns **per worker** (raise if you hit Groq 429s) |

Groq **on_demand** tiers are often capped around **~30 requests/minute**; the script backs off on `429`, but very aggressive settings will still error.

Stop `main.py` first so port `9100` is free.

**Security:** never commit API keys. If a key was pasted into chat or a screenshot, rotate it in the Groq console.
