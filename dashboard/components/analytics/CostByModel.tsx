"use client"

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts"
import type { CostByModel } from "@/lib/types"

interface Props {
  data: CostByModel[]
}

const COLORS = [
  "#6366f1", "#818cf8", "#a5b4fc",
  "#38bdf8", "#34d399", "#fb923c",
  "#f472b6", "#a78bfa", "#fbbf24",
]

function fmt(v: number) {
  return v < 0.01 ? `$${v.toFixed(5)}` : `$${v.toFixed(4)}`
}

export function CostByModel({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-600">
        No data yet
      </div>
    )
  }

  const sorted = [...data].sort((a, b) => b.cost_usd - a.cost_usd)

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart
        data={sorted}
        layout="vertical"
        margin={{ top: 4, right: 12, left: 0, bottom: 0 }}
      >
        <XAxis
          type="number"
          tick={{ fill: "#64748b", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={fmt}
        />
        <YAxis
          type="category"
          dataKey="model"
          tick={{ fill: "#94a3b8", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          width={140}
          tickFormatter={(v: string) => v.length > 18 ? v.slice(0, 17) + "…" : v}
        />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid #1e293b",
            borderRadius: 8,
            fontSize: 11,
          }}
          cursor={{ fill: "rgba(99,102,241,0.08)" }}
          formatter={(v) => [fmt(v as number), "Cost"]}
        />
        <Bar dataKey="cost_usd" radius={[0, 4, 4, 0]}>
          {sorted.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
