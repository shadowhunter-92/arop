"use client"

import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { ApiFilters } from "@/lib/types"

interface Props {
  filters: ApiFilters
  onChange: (f: ApiFilters) => void
}

const MODELS = [
  "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
  "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-sonnet-4-6",
  "gemini-1.5-pro", "gemini-2.0-flash",
]

export function TraceFilters({ filters, onChange }: Props) {
  const set = (patch: Partial<ApiFilters>) => onChange({ ...filters, ...patch, offset: 0 })

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {/* Status */}
      <Select
        value={filters.status ?? "all"}
        onValueChange={(v) => set({ status: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="w-36 h-8 text-xs bg-slate-900 border-slate-700">
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="success">Success</SelectItem>
          <SelectItem value="blocked">Blocked</SelectItem>
          <SelectItem value="error">Error</SelectItem>
        </SelectContent>
      </Select>

      {/* Model */}
      <Select
        value={filters.model ?? "all"}
        onValueChange={(v) => set({ model: v === "all" ? undefined : v })}
      >
        <SelectTrigger className="w-52 h-8 text-xs bg-slate-900 border-slate-700">
          <SelectValue placeholder="All models" />
        </SelectTrigger>
        <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
          <SelectItem value="all">All models</SelectItem>
          {MODELS.map((m) => (
            <SelectItem key={m} value={m}>{m}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* User ID */}
      <Input
        className="w-40 h-8 text-xs bg-slate-900 border-slate-700 placeholder:text-slate-600"
        placeholder="User ID"
        value={filters.user_id ?? ""}
        onChange={(e) => set({ user_id: e.target.value || undefined })}
      />

      {/* Feature */}
      <Input
        className="w-36 h-8 text-xs bg-slate-900 border-slate-700 placeholder:text-slate-600"
        placeholder="Feature tag"
        value={filters.feature ?? ""}
        onChange={(e) => set({ feature: e.target.value || undefined })}
      />

      {/* From date */}
      <input
        type="date"
        className="h-8 px-2 text-xs rounded-md bg-slate-900 border border-slate-700 text-slate-300"
        value={filters.from ? filters.from.slice(0, 10) : ""}
        onChange={(e) => set({ from: e.target.value ? e.target.value + "T00:00:00Z" : undefined })}
      />
      <span className="text-slate-600 text-xs">→</span>
      <input
        type="date"
        className="h-8 px-2 text-xs rounded-md bg-slate-900 border border-slate-700 text-slate-300"
        value={filters.to ? filters.to.slice(0, 10) : ""}
        onChange={(e) => set({ to: e.target.value ? e.target.value + "T23:59:59Z" : undefined })}
      />

      {/* Clear */}
      {Object.values(filters).some(Boolean) && (
        <button
          onClick={() => onChange({ limit: 50, offset: 0 })}
          className="text-xs text-slate-500 hover:text-slate-300 underline underline-offset-2"
        >
          Clear
        </button>
      )}
    </div>
  )
}
