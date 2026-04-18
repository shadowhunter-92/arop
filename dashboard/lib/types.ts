export interface Trace {
  id: string
  trace_id: string
  user_id: string | null
  feature: string | null
  model: string
  provider: string
  latency_ms: number | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  cost_usd: number | null
  status: "success" | "blocked" | "error"
  guardrail_hits: string[] | null
  parent_trace_id: string | null
  custom_score: number | null
  created_at: string
}

export interface TraceDetail extends Trace {
  request_body: Record<string, unknown> | null
  response_body: Record<string, unknown> | null
  prompt_hash: string | null
  response_hash: string | null
}

export interface TraceListResponse {
  traces: Trace[]
  total: number
}

export interface Guardrail {
  id: string
  name: string
  type: "pre_request" | "post_response"
  pattern: string
  action: "block" | "redact"
  enabled: boolean
  created_at: string
}

export interface GuardrailCreate {
  name: string
  type: "pre_request" | "post_response"
  pattern: string
  action: "block" | "redact"
}

export interface ReplayResponse {
  original_trace: TraceDetail
  replay_response: Record<string, unknown>
  replay_trace_id: string
  model_used: string
  latency_ms: number
  cost_usd: number
}

export interface CostDataPoint {
  date: string
  cost_usd: number
  total_tokens: number
  call_count: number
}

export interface CostByModel {
  model: string
  cost_usd: number
  call_count: number
}

export interface CostByFeature {
  feature: string
  cost_usd: number
  call_count: number
}

export interface CostAnalytics {
  over_time: CostDataPoint[]
  by_model: CostByModel[]
  by_feature: CostByFeature[]
  total_cost_usd: number
  total_calls: number
}

export interface ModelPricing {
  model: string
  provider: string
  prompt_cost_per_1m: number
  completion_cost_per_1m: number
  updated_at: string
}

export interface ApiFilters {
  model?: string
  user_id?: string
  feature?: string
  status?: string
  from?: string
  to?: string
  limit?: number
  offset?: number
}
