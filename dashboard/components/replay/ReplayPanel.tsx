"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import type { ReplayResponse } from "@/lib/types"
import { DiffView } from "./DiffView"

interface Props {
  traceId: string
  originalResponse?: unknown
  requestBody?: unknown
}

export function ReplayPanel({ traceId, originalResponse, requestBody }: Props) {
  const [promptOverride, setPromptOverride] = useState("")
  const [replaying, setReplaying] = useState(false)
  const [result, setResult] = useState<ReplayResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function replay() {
    setReplaying(true)
    setError(null)
    setResult(null)
    try {
      const overrideMessages = promptOverride
        ? [{ role: "user", content: promptOverride }]
        : undefined
      const res = await api.replay({
        trace_id: traceId,
        prompt_override: overrideMessages,
      })
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Replay failed")
    } finally {
      setReplaying(false)
    }
  }

  const origText = originalResponse
    ? JSON.stringify(originalResponse, null, 2)
    : null

  const newText = result?.replay_response
    ? JSON.stringify(result.replay_response, null, 2)
    : null

  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs text-slate-400 mb-2 font-medium">Prompt override</p>
        <p className="text-[11px] text-slate-600 mb-2">
          Leave blank to replay with the original prompt. Override to test a variation.
        </p>
        <textarea
          className="w-full h-28 px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 placeholder:text-slate-600 resize-y font-mono leading-relaxed"
          placeholder="Override system or user message here…"
          value={promptOverride}
          onChange={(e) => setPromptOverride(e.target.value)}
        />
      </div>

      <Button
        size="sm"
        className="h-8 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
        onClick={replay}
        disabled={replaying}
      >
        {replaying ? "Replaying…" : "↺ Run Replay"}
      </Button>

      {error && (
        <p className="text-xs text-red-400 bg-red-950/30 border border-red-900/50 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>Replay trace: <span className="font-mono text-slate-400">{result.replay_trace_id}</span></span>
            <span>Latency: <span className="text-slate-300">{result.latency_ms}ms</span></span>
            <span>Cost: <span className="text-slate-300">${result.cost_usd?.toFixed(6) ?? "—"}</span></span>
          </div>

          {origText && newText ? (
            <DiffView original={origText} updated={newText} />
          ) : (
            <pre className="text-xs bg-slate-900 border border-slate-800 rounded-lg p-4 overflow-x-auto text-slate-300 leading-relaxed">
              {newText}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
