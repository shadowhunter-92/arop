"use client"

interface Props {
  original: string
  updated: string
}

function diffLines(a: string, b: string) {
  const aLines = a.split("\n")
  const bLines = b.split("\n")
  const result: Array<{ type: "same" | "removed" | "added"; text: string }> = []

  const aSet = new Set(aLines)
  const bSet = new Set(bLines)

  const maxLen = Math.max(aLines.length, bLines.length)
  let ai = 0
  let bi = 0

  while (ai < aLines.length || bi < bLines.length) {
    const aLine = aLines[ai]
    const bLine = bLines[bi]

    if (ai >= aLines.length) {
      result.push({ type: "added", text: bLine })
      bi++
    } else if (bi >= bLines.length) {
      result.push({ type: "removed", text: aLine })
      ai++
    } else if (aLine === bLine) {
      result.push({ type: "same", text: aLine })
      ai++
      bi++
    } else {
      result.push({ type: "removed", text: aLine })
      result.push({ type: "added", text: bLine })
      ai++
      bi++
    }
  }

  return result
}

export function DiffView({ original, updated }: Props) {
  const lines = diffLines(original, updated)
  const hasChanges = lines.some((l) => l.type !== "same")

  if (!hasChanges) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3">
        <p className="text-xs text-slate-500 italic">Response identical to original.</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-800 overflow-hidden">
      <div className="px-4 py-2 border-b border-slate-800 bg-slate-900/60 flex items-center gap-4 text-[11px] text-slate-500">
        <span><span className="text-red-400 font-mono">−</span> removed</span>
        <span><span className="text-emerald-400 font-mono">+</span> added</span>
      </div>
      <pre className="text-xs overflow-x-auto leading-relaxed">
        {lines.map((line, i) => (
          <div
            key={i}
            className={
              line.type === "removed"
                ? "bg-red-950/40 text-red-300 px-4"
                : line.type === "added"
                ? "bg-emerald-950/40 text-emerald-300 px-4"
                : "text-slate-400 px-4"
            }
          >
            <span className="select-none mr-2 text-slate-600 font-mono">
              {line.type === "removed" ? "−" : line.type === "added" ? "+" : " "}
            </span>
            {line.text}
          </div>
        ))}
      </pre>
    </div>
  )
}
