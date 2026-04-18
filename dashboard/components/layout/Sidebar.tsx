"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const NAV = [
  { href: "/traces",     label: "Traces",     icon: "◈" },
  { href: "/analytics",  label: "Analytics",  icon: "◉" },
  { href: "/guardrails", label: "Guardrails", icon: "◎" },
  { href: "/settings",   label: "Settings",   icon: "◌" },
]

export function Sidebar() {
  const path = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-56 bg-slate-950 border-r border-slate-800 flex flex-col z-30">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-indigo-400 text-xl font-bold tracking-tight">AROP</span>
          <span className="text-[10px] text-slate-500 border border-slate-700 rounded px-1 py-0.5 uppercase tracking-wider">
            mvp
          </span>
        </div>
        <p className="text-[11px] text-slate-500 mt-0.5">AI Observability</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon }) => {
          const active = path === href || path.startsWith(href + "/")
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                active
                  ? "bg-indigo-500/15 text-indigo-300 font-medium"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              )}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-slate-800">
        <p className="text-[10px] text-slate-600">v0.1.0 · Sentinel</p>
      </div>
    </aside>
  )
}
