"use client"

import { useEffect, useState, useCallback } from "react"
import { TraceFilters } from "@/components/traces/TraceFilters"
import { TraceTable } from "@/components/traces/TraceTable"
import { api } from "@/lib/api"
import type { Trace, ApiFilters } from "@/lib/types"

export default function TracesPage() {
  const [filters, setFilters] = useState<ApiFilters>({ limit: 50, offset: 0 })
  const [traces, setTraces] = useState<Trace[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (f: ApiFilters) => {
    setLoading(true)
    try {
      const res = await api.traces.list(f)
      setTraces(res.traces)
      setTotal(res.total)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(filters)
  }, [filters, load])

  function handleFiltersChange(f: ApiFilters) {
    setFilters(f)
  }

  function handlePageChange(offset: number) {
    setFilters((f) => ({ ...f, offset }))
  }

  return (
    <div className="space-y-4">
      <TraceFilters filters={filters} onChange={handleFiltersChange} />
      <TraceTable
        traces={traces}
        total={total}
        limit={filters.limit ?? 50}
        offset={filters.offset ?? 0}
        onPageChange={handlePageChange}
        loading={loading}
      />
    </div>
  )
}
