import type {
  ApiFilters,
  CostAnalytics,
  Guardrail,
  GuardrailCreate,
  ReplayResponse,
  TraceDetail,
  TraceListResponse,
} from "./types"

const BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const KEY =
  process.env.NEXT_PUBLIC_AROP_KEY ?? ""

async function req<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": KEY,
      ...options.headers,
    },
    // Disable Next.js data cache so the dashboard always reflects live data
    cache: "no-store",
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  // 204 No Content
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

function qs(params: Record<string, string | number | undefined>): string {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") p.set(k, String(v))
  }
  const s = p.toString()
  return s ? `?${s}` : ""
}

export const api = {
  traces: {
    list: (filters: ApiFilters = {}): Promise<TraceListResponse> =>
      req(`/v1/traces${qs(filters as Record<string, string | number | undefined>)}`),

    get: (traceId: string): Promise<TraceDetail> =>
      req(`/v1/traces/${traceId}`),
  },

  guardrails: {
    list: (): Promise<Guardrail[]> =>
      req("/v1/guardrails"),

    create: (data: GuardrailCreate): Promise<Guardrail> =>
      req("/v1/guardrails", { method: "POST", body: JSON.stringify(data) }),

    toggle: (id: string, enabled: boolean): Promise<Guardrail> =>
      req(`/v1/guardrails/${id}/toggle`, {
        method: "PATCH",
        body: JSON.stringify({ enabled }),
      }),

    delete: (id: string): Promise<void> =>
      req(`/v1/guardrails/${id}`, { method: "DELETE" }),
  },

  replay: (payload: {
    trace_id: string
    model_override?: string
    prompt_override?: Array<{ role: string; content: string }>
  }): Promise<ReplayResponse> =>
    req("/v1/replay", { method: "POST", body: JSON.stringify(payload) }),

  evaluate: (trace_id: string, score: number, label?: string): Promise<void> =>
    req("/v1/evaluate", {
      method: "POST",
      body: JSON.stringify({ trace_id, score, label }),
    }),

  analytics: {
    cost: (from?: string, to?: string): Promise<CostAnalytics> =>
      req(`/v1/analytics/cost${qs({ from, to })}`),
  },
}
