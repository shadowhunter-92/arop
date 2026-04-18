"use client"

import { Suspense, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { ReplayPanel } from "@/components/replay/ReplayPanel"
import { api } from "@/lib/api"
import type { TraceDetail } from "@/lib/types"

function ReplayContent() {
  const params = useSearchParams()
  const traceId = params.get("trace_id") ?? ""
  const [trace, setTrace] = useState<TraceDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [manualId, setManualId] = useState(traceId)

  async function loadTrace(id: string) {
    if (!id.trim()) return
    setLoading(true)
    setError(null)
    try {
      const t = await api.traces.get(id.trim())
      setTrace(t)
    } catch {
      setError("Trace not found")
      setTrace(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (traceId) loadTrace(traceId)
  }, [traceId])

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3">
        <p className="text-xs text-slate-400 font-medium">Trace ID</p>
        <div className="flex items-center gap-2">
          <input
            className="flex-1 h-8 px-3 text-xs bg-slate-900 border border-slate-700 rounded-md text-slate-200 font-mono placeholder:text-slate-600"
            placeholder="Enter trace ID…"
            value={manualId}
            onChange={(e) => setManualId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadTrace(manualId)}
          />
          <button
            className="h-8 px-3 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded-md transition-colors"
            onClick={() => loadTrace(manualId)}
            disabled={loading}
          >
            {loading ? "Loading…" : "Load"}
          </button>
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>

      {trace && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-4">
          <div className="flex items-center gap-3">
            <p className="text-xs text-slate-400 font-medium">Replaying</p>
            <span className="text-xs font-mono text-slate-500">{trace.trace_id}</span>
            {trace.model && (
              <span className="text-[10px] text-slate-600 border border-slate-700 rounded px-1.5 py-0.5">
                {trace.model}
              </span>
            )}
          </div>
          <ReplayPanel
            traceId={trace.trace_id}
            originalResponse={trace.response_body ?? undefined}
            requestBody={trace.request_body ?? undefined}
          />
        </div>
      )}

      {!trace && !loading && !traceId && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-6 py-12 text-center">
          <p className="text-sm text-slate-600">Enter a trace ID above to replay it.</p>
          <p className="text-xs text-slate-700 mt-1">
            Or click ↺ Replay on any trace in the explorer.
          </p>
        </div>
      )}
    </div>
  )
}

export default function ReplayPage() {
  return (
    <Suspense fallback={<div className="max-w-3xl mx-auto py-12 text-center text-sm text-slate-600">Loading…</div>}>
      <ReplayContent />
    </Suspense>
  )
}
