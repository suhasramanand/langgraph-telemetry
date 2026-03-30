# LangGraph-Telemetry

**LangGraph-Telemetry** exports LangGraph run telemetry to **Prometheus** and includes a small **Next.js** dashboard. It is **third-party open source** and is **not affiliated with or endorsed by** LangChain or LangGraph.

## Features

- **Streaming (`version="v2"`)** integration: `TelemetryStreamBridge` wraps `graph.stream` / `graph.astream` and records step timing and run counters
- **LLM usage**: `TelemetryCallbackHandler` records token counters from `on_llm_end` when usage metadata exists
- **Bounded Prometheus labels** (see [docs/metrics.md](docs/metrics.md))
- **Docker Compose** + **Prometheus** scrape config

## Python quickstart

```bash
cd packages/langgraph-telemetry
pip install -e .
```

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph_telemetry import TelemetryConfig, TelemetryStreamBridge, start_metrics_server

start_metrics_server(9100)


class State(TypedDict):
    n: int


def work(state: State) -> dict[str, int]:
    return {"n": state["n"] + 1}


g = StateGraph(State)
g.add_node("work", work)
g.add_edge(START, "work")
g.add_edge("work", END)
graph = g.compile()

cfg = TelemetryConfig(graph_name="my_agent")
bridge = TelemetryStreamBridge(config=cfg)

for chunk in bridge.stream({"n": 0}, stream_mode=["updates"]):
    print(chunk)
```

## Local demo stack

1. Run the example agent (metrics on **9100**):

   ```bash
   pip install -e packages/langgraph-telemetry
   python examples/basic_agent/main.py
   ```

2. Start Prometheus (**9090**):

   ```bash
   docker compose up -d
   ```

3. Optional — dashboard:

   ```bash
   cd dashboard && npm ci && cp .env.example .env.local && npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000).

## Documentation

- [docs/development.md](docs/development.md)
- [docs/metrics.md](docs/metrics.md)
- [docs/architecture.md](docs/architecture.md)

## License

MIT — see [LICENSE](LICENSE).
