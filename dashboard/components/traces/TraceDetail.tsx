"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { cn, formatCost, formatDate, formatLatency, formatTokens, statusColor } from "@/lib/utils"
import { api } from "@/lib/api"
import type { TraceDetail as TDetail } from "@/lib/types"

interface Props { trace: TDetail }

function JsonBlock({ data, label }: { data: unknown; label: string }) {
  const [open, setOpen] = useState(true)
  if (!data) return (
    <div className="text-xs text-slate-600 italic px-1">
      Not stored — <code className="text-slate-500">HASH_PAYLOADS=true, STORE_RAW=false</code>
    </div>
  )
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-xs text-slate-500 hover:text-slate-300 mb-1"
      >
        {open ? "▾" : "▸"} {label}
      </button>
      {open && (
        <pre className="text-xs bg-slate-900 border border-slate-800 rounded-lg p-4 overflow-x-auto text-slate-300 leading-relaxed">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start gap-4 py-2 border-b border-slate-800/50 last:border-0">
      <dt className="text-xs text-slate-500 w-36 shrink-0 pt-0.5">{label}</dt>
      <dd className="text-xs text-slate-200 font-mono break-all">{value ?? "—"}</dd>
    </div>
  )
}

export function TraceDetail({ trace }: Props) {
  const [score, setScore] = useState<string>("")
  const [evaluating, setEvaluating] = useState(false)
  const [evalDone, setEvalDone] = useState(false)

  async function submitScore() {
    const n = parseFloat(score)
    if (isNaN(n) || n < 0 || n > 1) return
    setEvaluating(true)
    try {
      await api.evaluate(trace.trace_id, n)
      setEvalDone(true)
    } finally {
      setEvaluating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={cn("text-[11px] px-1.5 py-0.5 rounded border font-medium", statusColor(trace.status))}>
              {trace.status}
            </span>
            <span className="text-xs text-slate-500 font-mono">{trace.trace_id}</span>
          </div>
          <p className="text-slate-400 text-xs">{formatDate(trace.created_at)}</p>
        </div>
        <Link
          href={`/replay?trace_id=${trace.trace_id}`}
          className="shrink-0"
        >
          <Button size="sm" className="h-8 bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
            ↺ Replay
          </Button>
        </Link>
      </div>

      {/* Metadata */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-1">
        <dl>
          <Row label="Model" value={trace.model} />
          <Row label="Provider" value={trace.provider} />
          <Row label="User ID" value={trace.user_id} />
          <Row label="Feature" value={trace.feature} />
          <Row label="Latency" value={formatLatency(trace.latency_ms)} />
          <Row label="Tokens" value={`${formatTokens(trace.prompt_tokens)} prompt / ${formatTokens(trace.completion_tokens)} completion`} />
          <Row label="Cost" value={formatCost(trace.cost_usd)} />
          <Row label="Guardrail hits" value={trace.guardrail_hits?.join(", ") || "none"} />
          <Row label="Parent trace" value={trace.parent_trace_id} />
          <Row label="Prompt hash" value={<span className="text-slate-500">{trace.prompt_hash}</span>} />
          <Row label="Response hash" value={<span className="text-slate-500">{trace.response_hash}</span>} />
          {trace.custom_score !== null && trace.custom_score !== undefined && (
            <Row label="Custom score" value={
              <span className={trace.custom_score >= 0.7 ? "text-emerald-400" : "text-red-400"}>
                {trace.custom_score.toFixed(2)}
              </span>
            } />
          )}
        </dl>
      </div>

      {/* Payload */}
      <div className="space-y-3">
        <JsonBlock data={trace.request_body} label="Request" />
        <JsonBlock data={trace.response_body} label="Response" />
      </div>

      {/* Evaluate */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-xs text-slate-400 mb-3 font-medium">Quality Score</p>
        <p className="text-[11px] text-slate-600 mb-3">
          Post a 0–1 score for this trace (thumbs up=1, thumbs down=0, custom evals in between).
          Stored as <code className="text-slate-500">custom_score</code> for analytics.
        </p>
        {evalDone ? (
          <p className="text-xs text-emerald-400">✓ Score saved</p>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={0} max={1} step={0.1}
              value={score}
              onChange={(e) => setScore(e.target.value)}
              placeholder="0.0 – 1.0"
              className="w-28 h-8 px-2 text-xs bg-slate-900 border border-slate-700 rounded-md text-slate-200"
            />
            <Button
              size="sm"
              variant="outline"
              className="h-8 text-xs border-slate-700 hover:bg-slate-800"
              onClick={submitScore}
              disabled={evaluating || !score}
            >
              {evaluating ? "Saving…" : "Save score"}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
