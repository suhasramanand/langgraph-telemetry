import { NextRequest } from "next/server";

function prometheusBase(): string {
  return (process.env.PROMETHEUS_URL || "http://127.0.0.1:9090").replace(/\/$/, "");
}

/** Server-side proxy to Prometheus instant query API. */
export async function GET(req: NextRequest): Promise<Response> {
  const q = req.nextUrl.searchParams.get("q");
  if (!q) {
    return Response.json({ error: "missing query parameter q" }, { status: 400 });
  }
  const url = new URL("/api/v1/query", prometheusBase());
  url.searchParams.set("query", q);
  const t = req.nextUrl.searchParams.get("time");
  if (t) url.searchParams.set("time", t);
  const res = await fetch(url.toString(), { cache: "no-store" });
  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") || "application/json" },
  });
}
