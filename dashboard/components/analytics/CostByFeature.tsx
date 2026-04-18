"use client"

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts"
import type { CostByFeature } from "@/lib/types"

interface Props {
  data: CostByFeature[]
}

const COLORS = [
  "#6366f1", "#38bdf8", "#34d399",
  "#fb923c", "#f472b6", "#a78bfa",
  "#fbbf24", "#818cf8", "#4ade80",
]

function fmt(v: number) {
  return v < 0.01 ? `$${v.toFixed(5)}` : `$${v.toFixed(4)}`
}

export function CostByFeature({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-600">
        No data yet
      </div>
    )
  }

  const sorted = [...data].sort((a, b) => b.cost_usd - a.cost_usd).slice(0, 9)

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={sorted}
          dataKey="cost_usd"
          nameKey="feature"
          cx="50%"
          cy="50%"
          outerRadius={80}
          innerRadius={44}
          strokeWidth={0}
        >
          {sorted.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid #1e293b",
            borderRadius: 8,
            fontSize: 11,
          }}
          formatter={(v: number) => [fmt(v), "Cost"]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v: string) => (
            <span style={{ color: "#94a3b8", fontSize: 10 }}>
              {v.length > 16 ? v.slice(0, 15) + "…" : v}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
