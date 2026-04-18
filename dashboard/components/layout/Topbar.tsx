"use client"

import { usePathname } from "next/navigation"

const TITLES: Record<string, string> = {
  "/traces":     "Trace Explorer",
  "/analytics":  "Cost & Usage",
  "/guardrails": "Guardrails",
  "/settings":   "Settings",
  "/replay":     "Replay",
}

export function Topbar() {
  const path = usePathname()
  const base = "/" + (path.split("/")[1] ?? "")
  const title = TITLES[base] ?? "AROP"

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-20">
      <h1 className="text-sm font-semibold text-slate-200 tracking-wide">{title}</h1>
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Proxy live
        </span>
      </div>
    </header>
  )
}
