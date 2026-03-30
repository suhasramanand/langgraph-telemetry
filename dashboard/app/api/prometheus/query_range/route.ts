import { NextRequest } from "next/server";

function prometheusBase(): string {
  return (process.env.PROMETHEUS_URL || "http://127.0.0.1:9090").replace(/\/$/, "");
}

/** Server-side proxy to Prometheus range query API. */
export async function GET(req: NextRequest): Promise<Response> {
  const q = req.nextUrl.searchParams.get("q");
  const start = req.nextUrl.searchParams.get("start");
  const end = req.nextUrl.searchParams.get("end");
  const step = req.nextUrl.searchParams.get("step") || "30";
  if (!q || start === null || end === null) {
    return Response.json({ error: "missing q, start, or end" }, { status: 400 });
  }
  const url = new URL("/api/v1/query_range", prometheusBase());
  url.searchParams.set("query", q);
  url.searchParams.set("start", start);
  url.searchParams.set("end", end);
  url.searchParams.set("step", step);
  const res = await fetch(url.toString(), { cache: "no-store" });
  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") || "application/json" },
  });
}
