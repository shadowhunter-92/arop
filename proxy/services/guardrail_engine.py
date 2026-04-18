"""
Guardrail engine — pure functions, no DB access, no I/O.

Risk mitigation addressed here:
- Pre-request blocking prevents sensitive prompts from reaching the LLM (cost + compliance).
- Post-response PII redaction stops accidental data leaks before the client receives output.
- Rules are loaded from DB by the proxy router (with a 30-second cache) and passed in here,
  keeping this module stateless and trivially testable.

NOTE — Semantic guardrails (embedding-based relevance / off-topic detection) are planned
for v1.1 but intentionally excluded from MVP. The interface is designed so the semantic
check can be added as an additional function that accepts the same rule list format — no
breaking changes required when that feature lands.
"""
import re


# Built-in PII patterns applied on every post-response redaction pass.
# These run regardless of user-defined rules so that basic privacy protection
# is always on by default (opt-out is not available — risk: liability).
_BUILTIN_PII_PATTERNS: dict[str, str] = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b",
    "SSN":   r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
}


def check_pre_request(text: str, rules: list[dict]) -> tuple[bool, list[str]]:
    """
    Check whether a prompt should be blocked before forwarding to the LLM.

    Returns (blocked, list_of_triggered_rule_names).
    Only rules with type="pre_request" and action="block" are evaluated.
    """
    hits: list[str] = []
    for rule in rules:
        if not rule.get("enabled"):
            continue
        if rule.get("type") != "pre_request":
            continue
        if rule.get("action") != "block":
            continue
        try:
            if re.search(rule["pattern"], text, re.IGNORECASE | re.DOTALL):
                hits.append(rule["name"])
        except re.error:
            # Malformed regex in a user-defined rule — skip silently rather than
            # crashing the proxy. The rule should be fixed via the guardrails API.
            pass
    return bool(hits), hits


def redact_post_response(text: str, rules: list[dict]) -> str:
    """
    Redact PII and user-defined patterns from LLM response text before it is
    returned to the client or stored.

    Always applies built-in PII patterns. Also applies any enabled
    post_response rules with action="redact" from the user-defined rule list.
    """
    # Built-in PII pass (always runs)
    for label, pattern in _BUILTIN_PII_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED-{label}]", text, flags=re.IGNORECASE)

    # User-defined redact rules
    for rule in rules:
        if not rule.get("enabled"):
            continue
        if rule.get("type") != "post_response":
            continue
        if rule.get("action") != "redact":
            continue
        try:
            text = re.sub(rule["pattern"], "[REDACTED]", text, flags=re.IGNORECASE)
        except re.error:
            pass

    return text


def compute_hallucination_heuristic(response_text: str) -> float:
    """
    Lightweight hallucination proxy score (0.0 = likely fine, 1.0 = likely problematic).

    This is a placeholder heuristic based on length and repetition — NOT a real
    hallucination detector. It flags responses that are suspiciously short (no content)
    or suspiciously repetitive (model stuck in a loop), both known failure modes.

    A proper semantic hallucination detector (compare response to retrieved context
    using embeddings) is planned for v1.1.
    """
    if not response_text or len(response_text.strip()) < 10:
        return 1.0  # empty / too short — likely an error

    words = response_text.lower().split()
    if len(words) == 0:
        return 1.0

    unique_ratio = len(set(words)) / len(words)
    # Low unique word ratio → high repetition → suspicious
    # Threshold chosen empirically; tighten in v1.1 once we have ground-truth data.
    repetition_score = max(0.0, 1.0 - (unique_ratio * 2))

    return round(min(repetition_score, 1.0), 4)
