"""
Pure unit tests for guardrail_engine — no DB, no I/O, runs instantly.
"""
import pytest
from services.guardrail_engine import (
    check_pre_request,
    compute_hallucination_heuristic,
    redact_post_response,
)

CC_RULE = {
    "name": "block_cc",
    "type": "pre_request",
    "action": "block",
    "enabled": True,
    "pattern": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
}

REDACT_RULE = {
    "name": "redact_secret",
    "type": "post_response",
    "action": "redact",
    "enabled": True,
    "pattern": r"SECRET-\d+",
}


# ── check_pre_request ─────────────────────────────────────────────────────────

def test_pre_request_blocks_credit_card():
    blocked, hits = check_pre_request("my card is 4111 1111 1111 1111", [CC_RULE])
    assert blocked
    assert "block_cc" in hits


def test_pre_request_blocks_compact_credit_card():
    blocked, hits = check_pre_request("4111111111111111 is my card", [CC_RULE])
    assert blocked


def test_pre_request_passes_safe_prompt():
    blocked, hits = check_pre_request("What is 2 + 2?", [CC_RULE])
    assert not blocked
    assert hits == []


def test_pre_request_skips_disabled_rule():
    rule = {**CC_RULE, "enabled": False}
    blocked, _ = check_pre_request("4111 1111 1111 1111", [rule])
    assert not blocked


def test_pre_request_skips_post_response_rule():
    rule = {**CC_RULE, "type": "post_response"}
    blocked, _ = check_pre_request("4111 1111 1111 1111", [rule])
    assert not blocked


def test_pre_request_skips_redact_action():
    rule = {**CC_RULE, "action": "redact"}
    blocked, _ = check_pre_request("4111 1111 1111 1111", [rule])
    assert not blocked


def test_pre_request_multiple_rules_all_hit():
    rule2 = {"name": "block_word", "type": "pre_request", "action": "block",
             "enabled": True, "pattern": r"\bbomb\b"}
    blocked, hits = check_pre_request("bomb 4111 1111 1111 1111", [CC_RULE, rule2])
    assert blocked
    assert len(hits) == 2


def test_pre_request_invalid_regex_skipped():
    rule = {"name": "bad", "type": "pre_request", "action": "block",
            "enabled": True, "pattern": r"[invalid"}
    blocked, _ = check_pre_request("anything", [rule])
    assert not blocked


def test_pre_request_empty_rules():
    blocked, hits = check_pre_request("4111 1111 1111 1111", [])
    assert not blocked


# ── redact_post_response ──────────────────────────────────────────────────────

def test_redacts_email():
    result = redact_post_response("contact foo@example.com for info", [])
    assert "foo@example.com" not in result
    assert "[REDACTED-EMAIL]" in result


def test_redacts_phone():
    result = redact_post_response("call 555-123-4567 now", [])
    assert "555-123-4567" not in result
    assert "[REDACTED-PHONE]" in result


def test_redacts_ssn():
    result = redact_post_response("SSN is 123-45-6789", [])
    assert "123-45-6789" not in result
    assert "[REDACTED-SSN]" in result


def test_redacts_credit_card():
    result = redact_post_response("card 4111 1111 1111 1111 approved", [])
    assert "4111 1111 1111 1111" not in result


def test_user_defined_redact_rule():
    result = redact_post_response("the code is SECRET-9999", [REDACT_RULE])
    assert "SECRET-9999" not in result
    assert "[REDACTED]" in result


def test_clean_text_unchanged():
    text = "The answer to the question is forty-two."
    assert redact_post_response(text, []) == text


def test_redact_invalid_regex_skipped():
    rule = {"name": "bad", "type": "post_response", "action": "redact",
            "enabled": True, "pattern": r"[invalid"}
    result = redact_post_response("hello world", [rule])
    assert result == "hello world"


# ── compute_hallucination_heuristic ──────────────────────────────────────────

def test_empty_string_scores_one():
    assert compute_hallucination_heuristic("") == 1.0


def test_whitespace_only_scores_one():
    assert compute_hallucination_heuristic("   ") == 1.0


def test_very_short_scores_one():
    assert compute_hallucination_heuristic("ok") == 1.0


def test_diverse_text_scores_low():
    text = "The quick brown fox jumps over the lazy dog near the river bank"
    score = compute_hallucination_heuristic(text)
    assert score < 0.5


def test_highly_repetitive_scores_high():
    text = "yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes"
    score = compute_hallucination_heuristic(text)
    assert score > 0.5


def test_score_in_range():
    for text in ["hello", "a b c d e f g", "x " * 50]:
        score = compute_hallucination_heuristic(text)
        assert 0.0 <= score <= 1.0
