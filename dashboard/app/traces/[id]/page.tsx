"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { TraceDetail } from "@/components/traces/TraceDetail"
import { ReplayPanel } from "@/components/replay/ReplayPanel"
import { api } from "@/lib/api"
import type { TraceDetail as TDetail } from "@/lib/types"

export default function TraceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [trace, setTrace] = useState<TDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.traces.get(id)
      .then(setTrace)
      .catch(() => setError("Trace not found"))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-600">
        Loading…
      </div>
    )
  }

  if (error || !trace) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3">
        <p className="text-sm text-slate-500">{error ?? "Trace not found"}</p>
        <button
          onClick={() => router.push("/traces")}
          className="text-xs text-indigo-400 hover:text-indigo-300 underline underline-offset-2"
        >
          ← Back to traces
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button
        onClick={() => router.push("/traces")}
        className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
      >
        ← Back to traces
      </button>

      <TraceDetail trace={trace} />

      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-xs text-slate-400 mb-4 font-medium">Replay</p>
        <ReplayPanel
          traceId={trace.trace_id}
          originalResponse={trace.response_body ?? undefined}
          requestBody={trace.request_body ?? undefined}
        />
      </div>
    </div>
  )
}
