"use client"

import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { cn, formatCost, formatDate, formatLatency, formatTokens, statusColor } from "@/lib/utils"
import type { Trace } from "@/lib/types"

interface Props {
  traces: Trace[]
  total: number
  limit: number
  offset: number
  onPageChange: (offset: number) => void
  loading?: boolean
}

export function TraceTable({ traces, total, limit, offset, onPageChange, loading }: Props) {
  const router = useRouter()
  const page = Math.floor(offset / limit) + 1
  const pages = Math.max(1, Math.ceil(total / limit))

  return (
    <div className="flex flex-col gap-3">
      <div className="rounded-lg border border-slate-800 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-500 text-xs w-40">Time</TableHead>
              <TableHead className="text-slate-500 text-xs">Model</TableHead>
              <TableHead className="text-slate-500 text-xs">User</TableHead>
              <TableHead className="text-slate-500 text-xs">Feature</TableHead>
              <TableHead className="text-slate-500 text-xs text-right">Latency</TableHead>
              <TableHead className="text-slate-500 text-xs text-right">Tokens</TableHead>
              <TableHead className="text-slate-500 text-xs text-right">Cost</TableHead>
              <TableHead className="text-slate-500 text-xs">Status</TableHead>
              <TableHead className="text-slate-500 text-xs">Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={9} className="text-center text-slate-600 py-12 text-sm">
                  Loading…
                </TableCell>
              </TableRow>
            )}
            {!loading && traces.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} className="text-center text-slate-600 py-12 text-sm">
                  No traces yet. Point your AI calls at the proxy to start logging.
                </TableCell>
              </TableRow>
            )}
            {traces.map((t) => (
              <TableRow
                key={t.id}
                className="border-slate-800/60 cursor-pointer hover:bg-slate-800/40 transition-colors"
                onClick={() => router.push(`/traces/${t.trace_id}`)}
              >
                <TableCell className="text-slate-400 text-xs font-mono">
                  {formatDate(t.created_at)}
                </TableCell>
                <TableCell className="text-slate-200 text-xs font-mono">{t.model}</TableCell>
                <TableCell className="text-slate-400 text-xs">{t.user_id ?? "—"}</TableCell>
                <TableCell className="text-slate-400 text-xs">{t.feature ?? "—"}</TableCell>
                <TableCell className="text-slate-300 text-xs text-right font-mono">
                  {formatLatency(t.latency_ms)}
                </TableCell>
                <TableCell className="text-slate-300 text-xs text-right font-mono">
                  {formatTokens(t.total_tokens)}
                </TableCell>
                <TableCell className="text-slate-300 text-xs text-right font-mono">
                  {formatCost(t.cost_usd)}
                </TableCell>
                <TableCell>
                  <span className={cn("text-[10px] px-1.5 py-0.5 rounded border font-medium", statusColor(t.status))}>
                    {t.status}
                  </span>
                </TableCell>
                <TableCell className="text-slate-400 text-xs">
                  {t.custom_score !== null && t.custom_score !== undefined
                    ? <span className={t.custom_score >= 0.7 ? "text-emerald-400" : "text-red-400"}>
                        {t.custom_score.toFixed(2)}
                      </span>
                    : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>{total.toLocaleString()} total traces</span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-3 text-xs border-slate-700 bg-transparent hover:bg-slate-800"
            disabled={offset === 0}
            onClick={() => onPageChange(Math.max(0, offset - limit))}
          >
            ← Prev
          </Button>
          <span className="text-slate-400">{page} / {pages}</span>
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-3 text-xs border-slate-700 bg-transparent hover:bg-slate-800"
            disabled={offset + limit >= total}
            onClick={() => onPageChange(offset + limit)}
          >
            Next →
          </Button>
        </div>
      </div>
    </div>
  )
}
