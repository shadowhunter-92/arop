"use client"

import { useEffect, useState, useCallback } from "react"
import { ApiKeyManager } from "@/components/settings/ApiKeyManager"
import { Separator } from "@/components/ui/separator"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const MASTER_KEY = process.env.NEXT_PUBLIC_AROP_KEY ?? ""

interface ApiKey {
  id: number
  name: string
  created_at: string
  last_used_at: string | null
}

interface ModelPricing {
  id: number
  model: string
  provider: string
  prompt_cost_per_1m: number
  completion_cost_per_1m: number
  updated_at: string
}

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [pricing, setPricing] = useState<ModelPricing[]>([])
  const [loadingKeys, setLoadingKeys] = useState(true)
  const [loadingPricing, setLoadingPricing] = useState(true)

  const loadKeys = useCallback(async () => {
    setLoadingKeys(true)
    try {
      const res = await fetch(`${API_URL}/v1/settings/api-keys`, {
        headers: { "X-API-Key": MASTER_KEY },
        cache: "no-store",
      })
      if (res.ok) setApiKeys(await res.json())
    } finally {
      setLoadingKeys(false)
    }
  }, [])

  const loadPricing = useCallback(async () => {
    setLoadingPricing(true)
    try {
      const res = await fetch(`${API_URL}/v1/settings/pricing`, {
        headers: { "X-API-Key": MASTER_KEY },
        cache: "no-store",
      })
      if (res.ok) setPricing(await res.json())
    } finally {
      setLoadingPricing(false)
    }
  }, [])

  useEffect(() => {
    loadKeys()
    loadPricing()
  }, [loadKeys, loadPricing])

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* API Keys */}
      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-medium text-slate-200">API Keys</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Keys sent as <code className="text-slate-400">X-API-Key</code> header to authenticate proxy requests.
          </p>
        </div>
        {loadingKeys ? (
          <div className="text-xs text-slate-600 py-4">Loading…</div>
        ) : (
          <ApiKeyManager apiKeys={apiKeys} onRefresh={loadKeys} />
        )}
      </section>

      <Separator className="bg-slate-800" />

      {/* Model Pricing */}
      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-medium text-slate-200">Model Pricing</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Live rates used for cost calculation. Update via <code className="text-slate-400">PATCH /v1/settings/pricing/{"{model}"}</code>.
          </p>
        </div>
        {loadingPricing ? (
          <div className="text-xs text-slate-600 py-4">Loading…</div>
        ) : (
          <div className="rounded-lg border border-slate-800 divide-y divide-slate-800 overflow-hidden">
            <div className="grid grid-cols-4 gap-4 px-4 py-2 bg-slate-900/60 text-[10px] text-slate-500 uppercase tracking-wide">
              <span>Model</span>
              <span>Provider</span>
              <span className="text-right">Prompt / 1M</span>
              <span className="text-right">Completion / 1M</span>
            </div>
            {pricing.map((p) => (
              <div
                key={p.id}
                className="grid grid-cols-4 gap-4 px-4 py-2.5 bg-slate-900/20 text-xs"
              >
                <span className="text-slate-200 font-mono truncate">{p.model}</span>
                <span className="text-slate-500">{p.provider}</span>
                <span className="text-slate-300 text-right font-mono">${p.prompt_cost_per_1m.toFixed(2)}</span>
                <span className="text-slate-300 text-right font-mono">${p.completion_cost_per_1m.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <Separator className="bg-slate-800" />

      {/* Proxy endpoint */}
      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-medium text-slate-200">Proxy Endpoint</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Point your AI SDK base URL at this address.
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-500">Base URL</span>
            <code className="text-xs text-indigo-300 font-mono">{API_URL}/v1</code>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-500">Chat completions</span>
            <code className="text-xs text-slate-400 font-mono">{API_URL}/v1/chat/completions</code>
          </div>
        </div>
      </section>
    </div>
  )
}
