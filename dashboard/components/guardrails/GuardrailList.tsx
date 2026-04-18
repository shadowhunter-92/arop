"use client"

import { useState } from "react"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import type { Guardrail } from "@/lib/types"

interface Props {
  guardrails: Guardrail[]
  onRefresh: () => void
}

export function GuardrailList({ guardrails, onRefresh }: Props) {
  const [busy, setBusy] = useState<string | null>(null)

  async function toggle(id: string, enabled: boolean) {
    setBusy(id)
    try {
      await api.guardrails.toggle(id, enabled)
      onRefresh()
    } finally {
      setBusy(null)
    }
  }

  async function remove(id: string) {
    setBusy(id)
    try {
      await api.guardrails.delete(id)
      onRefresh()
    } finally {
      setBusy(null)
    }
  }

  if (guardrails.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-6 py-10 text-center">
        <p className="text-sm text-slate-600">No guardrails configured yet.</p>
        <p className="text-xs text-slate-700 mt-1">Add one below to start filtering requests.</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-800 divide-y divide-slate-800 overflow-hidden">
      {guardrails.map((g) => (
        <div
          key={g.id}
          className="flex items-center gap-4 px-4 py-3 bg-slate-900/20 hover:bg-slate-800/30 transition-colors"
        >
          <Switch
            checked={g.enabled}
            disabled={busy === g.id}
            onCheckedChange={(v: boolean) => toggle(g.id, v)}
            className="shrink-0"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-slate-200 font-medium">{g.name}</span>
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 border-slate-700 text-slate-400"
              >
                {g.type}
              </Badge>
              <Badge
                variant="outline"
                className={`text-[10px] px-1.5 ${
                  g.action === "block"
                    ? "border-red-900 text-red-400"
                    : "border-amber-900 text-amber-400"
                }`}
              >
                {g.action}
              </Badge>
            </div>
            <p className="text-[11px] text-slate-500 font-mono mt-0.5 truncate">{g.pattern}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-slate-600 hover:text-red-400 hover:bg-transparent shrink-0"
            disabled={busy === g.id}
            onClick={() => remove(g.id)}
            title="Delete guardrail"
          >
            ✕
          </Button>
        </div>
      ))}
    </div>
  )
}
