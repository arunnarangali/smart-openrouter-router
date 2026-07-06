#!/usr/bin/env python3
"""Tests for routing resolution and retry classification."""

import json

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from smart_router import select_candidates, should_retry


def make_model(id_: str) -> dict:
    return {"id": id_, "name": id_, "description": ""}


FREE_MODELS = [
    make_model("qwen/qwen3-coder:free"),
    make_model("qwen/qwen3-next-80b-a3b-instruct:free"),
    make_model("google/gemma-3-4b:free"),
    make_model("deepseek/deepseek-chat:free"),
]

RANKED_MODELS = list(FREE_MODELS)  # same dicts, just the "ranked" list
RANKED_IDS = [m["id"] for m in RANKED_MODELS]


def test_smart_router_best():
    candidates, tier, allowed, reason = select_candidates(RANKED_MODELS, FREE_MODELS, "smart-router/best")
    assert candidates == RANKED_IDS, f"Expected full ranked list, got {candidates}"
    assert tier == "free-ranked", f"Expected free-ranked tier, got {tier}"
    assert allowed is False, f"Expected requested not allowed, got {allowed}"
    assert reason == "smart-router-placeholder"


def test_smart_router_fast():
    candidates, tier, allowed, reason = select_candidates(RANKED_MODELS, FREE_MODELS, "smart-router/fast")
    assert candidates == RANKED_IDS, f"Expected full ranked list, got {candidates}"
    assert tier == "free-ranked"
    assert allowed is False
    assert reason == "smart-router-placeholder"


def test_smart_router_any():
    candidates, tier, allowed, reason = select_candidates(RANKED_MODELS, FREE_MODELS, "smart-router/")
    assert candidates == RANKED_IDS
    assert tier == "free-ranked"
    assert allowed is False
    assert reason == "smart-router-placeholder"


def test_exact_free_model():
    candidates, tier, allowed, reason = select_candidates(RANKED_MODELS, FREE_MODELS, "qwen/qwen3-coder:free")
    assert candidates[0] == "qwen/qwen3-coder:free"
    assert len(candidates) == len(RANKED_IDS)
    assert tier == "client-free-first"
    assert allowed is True
    assert reason == "free-model-first"


def test_paid_non_free():
    candidates, tier, allowed, reason = select_candidates(RANKED_MODELS, FREE_MODELS, "anthropic/claude-3-opus")
    assert candidates == RANKED_IDS
    assert tier == "client-nonfree-skipped"
    assert allowed is False
    assert reason == "not-free-or-not-found"


def test_empty_request():
    candidates, tier, allowed, reason = select_candidates(RANKED_MODELS, FREE_MODELS, "")
    assert candidates == RANKED_IDS
    assert tier == "free-ranked"
    assert allowed is False
    assert reason == "empty-request"


def test_context_length_error_retries():
    body = json.dumps({
        "error": {
            "message": "This endpoint's maximum context length is 32768 tokens. However, you requested about 40685 tokens (8685 of text input, 32000 in the output). Please reduce the length of either one, or use the context-compression plugin to compress your prompt automatically."
        }
    }).encode()

    assert should_retry(400, body) is True


def test_unrelated_bad_request_does_not_retry():
    body = json.dumps({"error": {"message": "Invalid request body"}}).encode()

    assert should_retry(400, body) is False


def main() -> int:
    test_smart_router_best()
    test_smart_router_fast()
    test_smart_router_any()
    test_exact_free_model()
    test_paid_non_free()
    test_empty_request()
    test_context_length_error_retries()
    test_unrelated_bad_request_does_not_retry()
    print("Routing resolution tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
