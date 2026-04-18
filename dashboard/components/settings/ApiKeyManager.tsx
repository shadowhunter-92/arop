"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { formatDate } from "@/lib/utils"

interface ApiKey {
  id: number
  name: string
  created_at: string
  last_used_at: string | null
}

interface Props {
  apiKeys: ApiKey[]
  onRefresh: () => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const MASTER_KEY = process.env.NEXT_PUBLIC_AROP_KEY ?? ""

export function ApiKeyManager({ apiKeys, onRefresh }: Props) {
  const [newName, setNewName] = useState("")
  const [creating, setCreating] = useState(false)
  const [created, setCreated] = useState<{ name: string; key: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function createKey() {
    if (!newName.trim()) return
    setCreating(true)
    setError(null)
    setCreated(null)
    try {
      const res = await fetch(`${API_URL}/v1/settings/api-keys`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": MASTER_KEY,
        },
        body: JSON.stringify({ name: newName.trim() }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setCreated({ name: data.name, key: data.raw_key })
      setNewName("")
      onRefresh()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create key")
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Existing keys */}
      <div className="rounded-lg border border-slate-800 divide-y divide-slate-800 overflow-hidden">
        {apiKeys.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs text-slate-600">
            No API keys yet.
          </div>
        ) : (
          apiKeys.map((k) => (
            <div key={k.id} className="flex items-center gap-4 px-4 py-3 bg-slate-900/20">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-200 font-medium">{k.name}</p>
                <p className="text-[11px] text-slate-600 mt-0.5">
                  Created {formatDate(k.created_at)}
                  {k.last_used_at && (
                    <> · Last used {formatDate(k.last_used_at)}</>
                  )}
                </p>
              </div>
              <span className="text-[10px] text-slate-600 font-mono">••••••••</span>
            </div>
          ))
        )}
      </div>

      {/* New key revealed after creation */}
      {created && (
        <div className="rounded-lg border border-emerald-800/60 bg-emerald-950/20 px-4 py-3 space-y-1">
          <p className="text-xs text-emerald-400 font-medium">Key created — copy now, won't be shown again</p>
          <code className="text-xs text-emerald-300 font-mono break-all">{created.key}</code>
        </div>
      )}

      {/* Create form */}
      <div className="flex items-center gap-2">
        <Input
          className="h-8 text-xs bg-slate-900 border-slate-700 w-52"
          placeholder="Key name (e.g. prod-app)"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && createKey()}
        />
        <Button
          size="sm"
          className="h-8 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
          onClick={createKey}
          disabled={creating || !newName.trim()}
        >
          {creating ? "Creating…" : "+ New Key"}
        </Button>
      </div>

      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}

      <p className="text-[11px] text-slate-600">
        Keys are SHA-256 hashed before storage. The raw key is only shown once at creation.
      </p>
    </div>
  )
}
