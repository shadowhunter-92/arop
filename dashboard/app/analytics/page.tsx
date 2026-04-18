"use client"

import { useEffect, useState } from "react"
import { CostOverTime } from "@/components/analytics/CostOverTime"
import { CostByModel } from "@/components/analytics/CostByModel"
import { CostByFeature } from "@/components/analytics/CostByFeature"
import { api } from "@/lib/api"
import { formatCost } from "@/lib/utils"
import type { CostAnalytics } from "@/lib/types"

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3">
      <p className="text-[11px] text-slate-500">{label}</p>
      <p className="text-xl font-semibold text-slate-100 mt-1 font-mono">{value}</p>
    </div>
  )
}

export default function AnalyticsPage() {
  const [data, setData] = useState<CostAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    setLoading(true)
    const to = new Date()
    const from = new Date(to.getTime() - days * 24 * 60 * 60 * 1000)
    api.analytics.cost(from.toISOString(), to.toISOString())
      .then(setData)
      .finally(() => setLoading(false))
  }, [days])

  const totalCost = data?.total_cost_usd ?? 0
  const totalTokens = data?.over_time.reduce((s, d) => s + (d.total_tokens ?? 0), 0) ?? 0
  const totalRequests = data?.total_calls ?? 0

  return (
    <div className="space-y-6">
      {/* Period picker */}
      <div className="flex items-center gap-2">
        {[7, 14, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
              days === d
                ? "bg-indigo-600 border-indigo-600 text-white"
                : "border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600"
            }`}
          >
            {d}d
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48 text-xs text-slate-600">
          Loading…
        </div>
      ) : (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Total cost" value={formatCost(totalCost)} />
            <StatCard label="Total tokens" value={totalTokens.toLocaleString()} />
            <StatCard label="Total requests" value={totalRequests.toLocaleString()} />
          </div>

          {/* Cost over time */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
            <p className="text-xs text-slate-400 font-medium mb-4">Cost over time</p>
            <CostOverTime data={data?.over_time ?? []} />
          </div>

          {/* Side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-400 font-medium mb-4">Cost by model</p>
              <CostByModel data={data?.by_model ?? []} />
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-400 font-medium mb-4">Cost by feature</p>
              <CostByFeature data={data?.by_feature ?? []} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
