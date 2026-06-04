#!/usr/bin/env python3
"""Tests for select_candidates routing resolution."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from smart_router import select_candidates


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


def main() -> int:
    test_smart_router_best()
    test_smart_router_fast()
    test_smart_router_any()
    test_exact_free_model()
    test_paid_non_free()
    test_empty_request()
    print("Routing resolution tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
