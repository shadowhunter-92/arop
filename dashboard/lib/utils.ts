import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCost(usd: number | null): string {
  if (usd === null || usd === undefined) return "—"
  if (usd < 0.001) return `$${(usd * 1000).toFixed(4)}m`
  return `$${usd.toFixed(4)}`
}

export function formatTokens(n: number | null): string {
  if (n === null || n === undefined) return "—"
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

export function formatLatency(ms: number | null): string {
  if (ms === null || ms === undefined) return "—"
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function statusColor(status: string): string {
  return (
    {
      success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      blocked: "bg-amber-500/15 text-amber-400 border-amber-500/30",
      error:   "bg-red-500/15 text-red-400 border-red-500/30",
    }[status] ?? "bg-slate-500/15 text-slate-400 border-slate-500/30"
  )
}

export function providerColor(provider: string): string {
  return (
    {
      openai:    "text-green-400",
      anthropic: "text-orange-400",
      google:    "text-blue-400",
    }[provider] ?? "text-slate-400"
  )
}
