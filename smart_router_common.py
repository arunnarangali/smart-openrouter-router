#!/usr/bin/env python3
"""Shared constants and helpers for smart-openrouter-router."""

from __future__ import annotations

import json
from pathlib import Path


SCENARIOS = [
    "coding_general",
    "coding_frontend",
    "coding_backend",
    "coding_debugging",
    "coding_refactor",
    "coding_testing",
    "coding_devops",
    "coding_database",
    "coding_architecture",
    "coding_security",
    "coding_performance",
    "coding_mobile",
    "coding_ai_ml",
    "coding_docs",
    "coding_review",
    "reasoning_general",
    "reasoning_math",
    "reasoning_analysis",
    "reasoning_planning",
    "reasoning_architecture",
    "reasoning_debug",
    "reasoning_review",
    "reasoning_legal_policy",
    "reasoning_finance",
    "writing_general",
    "writing_docs",
    "writing_email",
    "writing_summary",
    "writing_rewrite",
    "research_general",
    "research_fact_check",
    "creative_general",
    "creative_story",
    "creative_marketing",
    "vision",
    "long_context",
    "fast",
]

SCENARIO_KEYWORDS = {
    "coding_general": {"code": 2, "function": 2, "class": 2, "implement": 2, "script": 2, "program": 2, "repository": 1},
    "coding_frontend": {"react": 4, "component": 3, "css": 3, "tailwind": 4, "ui": 3, "layout": 3, "frontend": 4, "typescript": 2, "javascript": 2, "responsive": 3},
    "coding_backend": {"api": 4, "endpoint": 3, "backend": 4, "server": 3, "auth": 3, "middleware": 3, "fastapi": 3, "flask": 3, "express": 3, "service": 2},
    "coding_debugging": {"debug": 4, "error": 3, "bug": 3, "traceback": 5, "stack trace": 5, "exception": 4, "failing": 3, "fix": 3, "crash": 4},
    "coding_refactor": {"refactor": 5, "cleanup": 3, "simplify": 3, "restructure": 3, "maintainability": 3, "readability": 2},
    "coding_testing": {"test": 3, "pytest": 4, "jest": 4, "mock": 3, "fixture": 3, "coverage": 3, "unit test": 4, "integration test": 4},
    "coding_devops": {"docker": 4, "kubernetes": 4, "ci": 3, "github actions": 4, "deploy": 3, "linux": 3, "bash": 3, "shell": 3, "nginx": 3},
    "coding_database": {"sql": 4, "postgres": 4, "mysql": 4, "sqlite": 3, "schema": 3, "migration": 3, "query": 3, "index": 3, "database": 4},
    "coding_architecture": {"architecture": 4, "design": 3, "scalable": 3, "module": 2, "monolith": 2, "microservice": 3},
    "coding_security": {"security": 4, "vulnerability": 4, "xss": 5, "csrf": 5, "injection": 4, "secret": 3, "permission": 3, "authz": 3},
    "coding_performance": {"performance": 4, "optimize": 4, "latency": 3, "memory": 3, "bottleneck": 3, "profiling": 3, "slow": 3},
    "coding_mobile": {"android": 4, "ios": 4, "react native": 5, "flutter": 5, "swift": 3, "kotlin": 3, "mobile": 4},
    "coding_ai_ml": {"llm": 4, "embedding": 4, "vector": 3, "rag": 4, "inference": 3, "model": 2, "agent": 3, "ml": 3},
    "coding_docs": {"readme": 4, "documentation": 4, "docstring": 3, "api docs": 4, "comment": 2},
    "coding_review": {"code review": 5, "review this code": 5, "regression": 3, "lint": 2, "smell": 2},
    "reasoning_general": {"reason": 2, "analyze": 2, "evaluate": 2, "consider": 2, "tradeoff": 2, "decision": 2, "logic": 2},
    "reasoning_math": {"math": 4, "equation": 4, "proof": 5, "formula": 4, "calculate": 3, "probability": 4, "theorem": 4},
    "reasoning_analysis": {"compare": 4, "pros and cons": 4, "trade-off": 4, "analysis": 3, "evaluate": 3},
    "reasoning_planning": {"plan": 4, "roadmap": 4, "step by step": 4, "strategy": 3, "milestone": 3},
    "reasoning_architecture": {"system design": 5, "architecture": 5, "scalable": 3, "distributed": 3, "tradeoff": 3},
    "reasoning_debug": {"root cause": 5, "why failed": 4, "diagnose": 4, "investigate failure": 4},
    "reasoning_review": {"critique": 4, "risk": 3, "review": 3, "assessment": 3, "concern": 2},
    "reasoning_legal_policy": {"policy": 4, "legal": 4, "compliance": 4, "regulation": 3, "license": 3, "terms": 3},
    "reasoning_finance": {"roi": 5, "budget": 4, "pricing": 4, "cost": 3, "revenue": 3, "profit": 3},
    "writing_general": {"write": 2, "draft": 2, "article": 2, "paragraph": 2, "tone": 2},
    "writing_docs": {"documentation": 4, "readme": 4, "guide": 3, "manual": 3, "tutorial": 3},
    "writing_email": {"email": 5, "reply": 4, "message": 3, "subject line": 3},
    "writing_summary": {"summarize": 5, "summary": 5, "key points": 4, "condense": 3},
    "writing_rewrite": {"rewrite": 5, "rephrase": 4, "improve": 3, "clarity": 3, "polish": 3},
    "research_general": {"research": 4, "search": 3, "look up": 3, "investigate": 3, "find information": 3},
    "research_fact_check": {"fact check": 5, "verify": 4, "source": 3, "evidence": 3, "accurate": 3},
    "creative_general": {"creative": 4, "invent": 3, "idea": 2, "brainstorm": 3},
    "creative_story": {"story": 5, "fiction": 4, "poem": 4, "narrative": 4, "character": 3, "plot": 3},
    "creative_marketing": {"marketing": 5, "ad": 4, "copy": 4, "hook": 4, "slogan": 4, "landing page": 4},
    "vision": {"image": 4, "photo": 4, "screenshot": 4, "ocr": 4, "visual": 3, "describe image": 4},
    "long_context": {"large file": 4, "full text": 4, "long document": 4, "chapter": 3, "book": 3, "pdf": 3},
    "fast": {"quick": 3, "fast": 4, "short answer": 3, "brief": 3},
}


def build_default_profiles() -> dict:
    default_profile = {
        "preferred": [],
        "prefer_patterns": [],
        "avoid_patterns": ["audio", "music", "tts", "embedding"],
        "min_context": 8000,
    }
    profiles = {name: dict(default_profile) for name in SCENARIOS}
    profiles["coding_general"].update({"prefer_patterns": ["coder", "code", "qwen", "deepseek", "instruct"], "min_context": 16000})
    profiles["reasoning_general"].update({"prefer_patterns": ["reasoning", "think", "r1", "qwq", "qwen", "deepseek"], "min_context": 32000})
    profiles["writing_general"].update({"prefer_patterns": ["llama", "gemma", "mistral", "chat", "instruct"], "min_context": 8000})
    profiles["vision"].update({"prefer_patterns": ["vision", "multimodal", "image", "pixel"], "avoid_patterns": ["tiny", "3b", "4b", "flash"], "min_context": 4096})
    profiles["long_context"].update({"prefer_patterns": ["large", "128k", "200k", "context"], "avoid_patterns": ["tiny", "3b"], "min_context": 32000})
    profiles["fast"].update({"prefer_patterns": ["flash", "mini", "small", "3b", "4b", "7b", "8b"], "avoid_patterns": ["405b", "120b", "large"], "min_context": 4096})
    profiles["research_general"].update({"prefer_patterns": ["flash", "mini", "small", "fast"], "min_context": 4096})
    profiles["creative_general"].update({"prefer_patterns": ["creative", "story", "gemma", "llama"], "min_context": 8192})
    return profiles


def _specificity(scenario: str) -> int:
    return 0 if scenario.endswith("_general") else 1


def analyze_prompt_text(text: str) -> dict:
    text_lc = str(text or "").lower()
    scores = {scenario: 0 for scenario in SCENARIOS}
    for scenario, keywords in SCENARIO_KEYWORDS.items():
        for keyword, weight in keywords.items():
            if keyword in text_lc:
                scores[scenario] += int(weight)

    detected = max(SCENARIOS, key=lambda s: (scores[s], _specificity(s)))
    if scores[detected] <= 0:
        detected = "reasoning_general"

    positive = sorted([(name, value) for name, value in scores.items() if value > 0], key=lambda item: item[1], reverse=True)
    top_score = positive[0][1] if positive else 0
    total = sum(value for _name, value in positive)
    confidence = round((top_score / total), 3) if total > 0 else 0.0
    return {
        "detected_scenario": detected,
        "scenario_scores": scores,
        "top_scenarios": positive[:5],
        "scenario_confidence": confidence,
    }


def is_text_chat_model(model: dict) -> bool:
    architecture = model.get("architecture") or {}
    modality = str(architecture.get("modality") or "").lower()
    input_modalities = {str(item).lower() for item in architecture.get("input_modalities", [])}
    output_modalities = {str(item).lower() for item in architecture.get("output_modalities", [])}

    if input_modalities and "text" not in input_modalities:
        return False
    if output_modalities and "text" not in output_modalities:
        return False
    if modality and "text" not in modality:
        return False

    combined = " ".join(str(model.get(field) or "").lower() for field in ["id", "name", "description"])
    blocked_terms = ["audio", "image", "video", "music", "lyria", "tts", "embedding"]
    return not any(term in combined for term in blocked_terms)


def filter_free_models(models: list[dict]) -> list[dict]:
    free: list[dict] = []
    for model in models:
        pricing = model.get("pricing", {})
        prompt_cost = float(pricing.get("prompt", "1") or "1")
        completion_cost = float(pricing.get("completion", "1") or "1")
        if prompt_cost == 0 and completion_cost == 0 and is_text_chat_model(model):
            free.append(model)
    return free


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)
