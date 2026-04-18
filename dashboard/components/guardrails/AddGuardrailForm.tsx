"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { api } from "@/lib/api"

interface Props {
  onCreated: () => void
}

export function AddGuardrailForm({ onCreated }: Props) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [type, setType] = useState<"pre_request" | "post_response">("pre_request")
  const [pattern, setPattern] = useState("")
  const [action, setAction] = useState<"block" | "redact">("block")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !pattern.trim()) return
    setSaving(true)
    setError(null)
    try {
      await api.guardrails.create({ name, type, pattern, action })
      setName("")
      setPattern("")
      setType("pre_request")
      setAction("block")
      setOpen(false)
      onCreated()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create guardrail")
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <Button
        size="sm"
        className="h-8 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
        onClick={() => setOpen(true)}
      >
        + Add Guardrail
      </Button>
    )
  }

  return (
    <form
      onSubmit={submit}
      className="rounded-lg border border-slate-700 bg-slate-900/60 p-4 space-y-4"
    >
      <p className="text-xs text-slate-300 font-medium">New Guardrail</p>

      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2 space-y-1">
          <Label className="text-[11px] text-slate-400">Name</Label>
          <Input
            className="h-8 text-xs bg-slate-900 border-slate-700"
            placeholder="e.g. Block PII"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div className="space-y-1">
          <Label className="text-[11px] text-slate-400">Stage</Label>
          <Select value={type} onValueChange={(v) => setType(v as typeof type)}>
            <SelectTrigger className="h-8 text-xs bg-slate-900 border-slate-700">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
              <SelectItem value="pre_request">Pre-request</SelectItem>
              <SelectItem value="post_response">Post-response</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-[11px] text-slate-400">Action</Label>
          <Select value={action} onValueChange={(v) => setAction(v as typeof action)}>
            <SelectTrigger className="h-8 text-xs bg-slate-900 border-slate-700">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
              <SelectItem value="block">Block (return 400)</SelectItem>
              <SelectItem value="redact">Redact</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="col-span-2 space-y-1">
          <Label className="text-[11px] text-slate-400">Regex pattern</Label>
          <Input
            className="h-8 text-xs bg-slate-900 border-slate-700 font-mono"
            placeholder="e.g. \b\d{16}\b"
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            required
          />
          <p className="text-[10px] text-slate-600">
            Python-compatible regex. Tested against full request/response text.
          </p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}

      <div className="flex items-center gap-2">
        <Button
          type="submit"
          size="sm"
          className="h-8 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
          disabled={saving}
        >
          {saving ? "Saving…" : "Save Guardrail"}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-8 text-xs text-slate-500 hover:text-slate-300"
          onClick={() => setOpen(false)}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
