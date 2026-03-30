import { PrometheusLineChart } from "@/components/PrometheusLineChart";

export const dynamic = "force-dynamic";

async function instantValue(query: string): Promise<string> {
  try {
    const base = process.env.PROMETHEUS_URL || "http://127.0.0.1:9090";
    const url = new URL("/api/v1/query", base.replace(/\/$/, ""));
    url.searchParams.set("query", query);
    const res = await fetch(url.toString(), { cache: "no-store" });
    if (!res.ok) return "—";
    const json: unknown = await res.json();
    if (
      json &&
      typeof json === "object" &&
      "data" in json &&
      json.data &&
      typeof json.data === "object" &&
      "result" in json.data &&
      Array.isArray(json.data.result) &&
      json.data.result[0] &&
      typeof json.data.result[0] === "object" &&
      "value" in json.data.result[0] &&
      Array.isArray(json.data.result[0].value)
    ) {
      const v = json.data.result[0].value[1];
      return String(v);
    }
    return "—";
  } catch {
    return "—";
  }
}

export default async function Home() {
  const promBase = (process.env.PROMETHEUS_URL || "http://127.0.0.1:9090").replace(/\/$/, "");

  const runs = await instantValue("sum(langgraph_graph_runs_total)");
  const updates = await instantValue("sum(langgraph_stream_updates_total)");
  const llmCalls = await instantValue("sum(langgraph_llm_calls_total)");
  const tokensPrompt = await instantValue('sum(langgraph_llm_tokens_total{token_type="prompt"})');
  const tokensCompletion = await instantValue('sum(langgraph_llm_tokens_total{token_type="completion"})');
  const tokensTotal = await instantValue('sum(langgraph_llm_tokens_total{token_type="total"})');

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur">
        <div className="mx-auto max-w-5xl px-6 py-5">
          <h1 className="text-xl font-semibold tracking-tight">LangGraph Telemetry</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
            Prometheus:{" "}
            <code className="text-xs bg-zinc-100 dark:bg-zinc-800 px-1 rounded break-all">{promBase}</code>
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-400 mt-2">
            Histogram quantiles need enough scrapes and samples — see docs/metrics.md in the repo.
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8 space-y-10">
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Graph runs (sum)</p>
            <p className="text-3xl font-mono mt-2">{runs}</p>
            <p className="text-xs text-zinc-500 mt-2">langgraph_graph_runs_total</p>
          </div>
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Stream updates (sum)</p>
            <p className="text-3xl font-mono mt-2">{updates}</p>
            <p className="text-xs text-zinc-500 mt-2">langgraph_stream_updates_total</p>
          </div>
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">LLM calls (sum)</p>
            <p className="text-3xl font-mono mt-2">{llmCalls}</p>
            <p className="text-xs text-zinc-500 mt-2">langgraph_llm_calls_total</p>
          </div>
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Tokens — prompt</p>
            <p className="text-3xl font-mono mt-2">{tokensPrompt}</p>
            <p className="text-xs text-zinc-500 mt-2">langgraph_llm_tokens_total (prompt)</p>
          </div>
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Tokens — completion</p>
            <p className="text-3xl font-mono mt-2">{tokensCompletion}</p>
            <p className="text-xs text-zinc-500 mt-2">langgraph_llm_tokens_total (completion)</p>
          </div>
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Tokens — total (usage)</p>
            <p className="text-3xl font-mono mt-2">{tokensTotal}</p>
            <p className="text-xs text-zinc-500 mt-2">langgraph_llm_tokens_total (total)</p>
          </div>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
            Stream update rate (5m rate window)
          </h2>
          <p className="text-xs text-zinc-500 mb-4 font-mono">
            sum(rate(langgraph_stream_updates_total[5m]))
          </p>
          <PrometheusLineChart
            promql="sum(rate(langgraph_stream_updates_total[5m]))"
            seriesName="updates/s"
          />
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
            Graph runs rate (5m rate window)
          </h2>
          <p className="text-xs text-zinc-500 mb-4 font-mono">
            sum(rate(langgraph_graph_runs_total[5m]))
          </p>
          <PrometheusLineChart
            promql="sum(rate(langgraph_graph_runs_total[5m]))"
            seriesName="runs/s"
          />
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
            LLM tokens / second (5m rate, usage total)
          </h2>
          <p className="text-xs text-zinc-500 mb-4 font-mono">
            {`sum(rate(langgraph_llm_tokens_total{token_type="total"}[5m]))`}
          </p>
          <PrometheusLineChart
            promql='sum(rate(langgraph_llm_tokens_total{token_type="total"}[5m]))'
            seriesName="tokens/s"
          />
        </section>
      </main>
    </div>
  );
}
