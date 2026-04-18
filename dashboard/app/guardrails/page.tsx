"use client"

import { useEffect, useState, useCallback } from "react"
import { GuardrailList } from "@/components/guardrails/GuardrailList"
import { AddGuardrailForm } from "@/components/guardrails/AddGuardrailForm"
import { api } from "@/lib/api"
import type { Guardrail } from "@/lib/types"

export default function GuardrailsPage() {
  const [guardrails, setGuardrails] = useState<Guardrail[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const data = await api.guardrails.list()
      setGuardrails(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 mt-0.5">
            Regex rules applied to every proxied request and response.
          </p>
        </div>
        <AddGuardrailForm onCreated={load} />
      </div>

      {loading ? (
        <div className="rounded-lg border border-slate-800 px-4 py-10 text-center text-xs text-slate-600">
          Loading…
        </div>
      ) : (
        <GuardrailList guardrails={guardrails} onRefresh={load} />
      )}

      <div className="rounded-lg border border-slate-800/60 bg-slate-900/20 px-4 py-3 space-y-1">
        <p className="text-[11px] text-slate-500 font-medium">Built-in PII redaction (always active)</p>
        <p className="text-[10px] text-slate-600">
          Email addresses, phone numbers, US SSNs, and credit card numbers are automatically
          redacted from all responses regardless of guardrail settings.
        </p>
      </div>
    </div>
  )
}
