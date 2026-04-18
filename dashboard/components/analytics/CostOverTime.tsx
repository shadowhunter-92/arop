"use client"

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts"
import type { CostDataPoint } from "@/lib/types"

interface Props {
  data: CostDataPoint[]
}

function fmt(v: number) {
  return v < 0.01 ? `$${v.toFixed(5)}` : `$${v.toFixed(4)}`
}

export function CostOverTime({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-600">
        No data yet
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#64748b", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis
          tick={{ fill: "#64748b", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={fmt}
          width={60}
        />
        <Tooltip
          contentStyle={{
            background: "#0f172a",
            border: "1px solid #1e293b",
            borderRadius: 8,
            fontSize: 11,
          }}
          labelStyle={{ color: "#94a3b8" }}
          formatter={(v: number) => [fmt(v), "Cost"]}
        />
        <Area
          type="monotone"
          dataKey="cost_usd"
          stroke="#6366f1"
          strokeWidth={2}
          fill="url(#costGrad)"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
