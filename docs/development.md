# Development

## Python package

```bash
cd packages/langgraph-telemetry
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check src tests && ruff format src tests
pytest tests/ -v
```

## Incremental testing

After code changes, run **ruff** and **pytest**. When changing metrics or the HTTP exporter, run `examples/basic_agent/main.py` and inspect `http://127.0.0.1:9100/metrics`.

If you are stuck after two fix attempts, search official LangGraph / Prometheus docs and issue trackers before guessing.

## Dashboard

```bash
cd dashboard
cp .env.example .env.local
# set PROMETHEUS_URL if Prometheus is not on localhost:9090
npm ci
npm run lint
npm run build
npm run dev
```

## Docker Compose

From the repository root:

```bash
docker compose up -d
```

Prometheus UI: [http://127.0.0.1:9090](http://127.0.0.1:9090)

The scrape target uses `host.docker.internal:9100` so a metrics server on your host (e.g. the example) is reachable from the container.

## Multi-process Python

If you run multiple Gunicorn/Uvicorn workers, use `prometheus_client`’s multiprocess mode and `PROMETHEUS_MULTIPROC_DIR` as documented for that library.
