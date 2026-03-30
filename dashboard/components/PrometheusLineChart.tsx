"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Row = { label: string; v: number };

function parseSample(s: string): number {
  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
}

type Props = {
  /** PromQL expression for Prometheus range query */
  promql: string;
  /** Legend / tooltip name for the Y value */
  seriesName: string;
  /** Default 30s */
  stepSec?: number;
  /** How far back to plot (seconds). Default 1h */
  lookbackSec?: number;
};

export function PrometheusLineChart({
  promql,
  seriesName,
  stepSec = 30,
  lookbackSec = 3600,
}: Props) {
  const [data, setData] = useState<Row[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const qEnc = encodeURIComponent(promql);

    async function load() {
      try {
        const end = Math.floor(Date.now() / 1000);
        const start = end - lookbackSec;
        const res = await fetch(
          `/api/prometheus/query_range?q=${qEnc}&start=${start}&end=${end}&step=${stepSec}`,
        );
        if (!res.ok) {
          throw new Error(await res.text());
        }
        const json: unknown = await res.json();
        const values =
          json &&
          typeof json === "object" &&
          "data" in json &&
          json.data &&
          typeof json.data === "object" &&
          "result" in json.data &&
          Array.isArray(json.data.result) &&
          json.data.result[0] &&
          typeof json.data.result[0] === "object" &&
          "values" in json.data.result[0] &&
          Array.isArray(json.data.result[0].values)
            ? (json.data.result[0].values as [string, string][])
            : [];
        const rows: Row[] = values.map(([ts, val]) => ({
          label: new Date(Number(ts) * 1000).toLocaleTimeString(),
          v: parseSample(val),
        }));
        if (!cancelled) {
          setData(rows);
          setErr(null);
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : String(e));
      }
    }

    void load();
    const id = setInterval(() => void load(), 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [promql, stepSec, lookbackSec]);

  if (err) {
    return <p className="text-red-600 text-sm">Prometheus: {err}</p>;
  }

  if (data.length === 0) {
    return (
      <p className="text-sm text-zinc-500 py-16 text-center">
        No range samples yet — wait for scrapes or shorten the lookback in Prometheus.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 4, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-300 dark:stroke-zinc-600 opacity-50" />
        <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" stroke="#71717a" />
        <YAxis
          tick={{ fontSize: 11 }}
          width={52}
          stroke="#71717a"
          domain={[0, "auto"]}
          allowDecimals
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#18181b",
            border: "1px solid #3f3f46",
            color: "#fafafa",
          }}
        />
        <Line
          type="monotone"
          dataKey="v"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
          name={seriesName}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
