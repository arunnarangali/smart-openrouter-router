#!/usr/bin/env python3
"""
Smart OpenRouter Proxy for Claude Code.

Listens on localhost, chooses a current free OpenRouter model based on the
request prompt, and forwards Claude Code requests to OpenRouter transparently.
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROXY_HOST = "127.0.0.1"
PROXY_PORT = int(os.environ.get("PROXY_PORT", "8080"))
OPENROUTER_ORIGIN = "https://openrouter.ai"
OPENROUTER_API_BASE = f"{OPENROUTER_ORIGIN}/api/v1"
CACHE_TTL = 1800
LOG_FILE = os.environ.get("SMART_ROUTER_LOG", os.path.expanduser("~/.smart_router.log"))
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "smart-openrouter-router"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "smart-openrouter-router"
CONFIG_FILE = CONFIG_DIR / "config.json"
COOLDOWNS_FILE = CACHE_DIR / "cooldowns.json"
STATS_FILE = CACHE_DIR / "stats.json"


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

CODING_TAGS = {"coding", "code", "programming", "instruct"}
REASONING_TAGS = {"reasoning", "math", "logic", "analysis"}
WRITING_TAGS = {"creative", "writing", "multilingual", "chat"}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("smart_router")


class ModelCache:
    def __init__(self):
        self._models = []
        self._last_fetch = 0
        self._lock = threading.Lock()

    def cache_age(self):
        with self._lock:
            return time.time() - self._last_fetch if self._last_fetch else -1

    def get_cached_models(self):
        with self._lock:
            return list(self._models)

    def get_free_models(self, api_key):
        with self._lock:
            if self._models and time.time() - self._last_fetch < CACHE_TTL:
                return self._models

            try:
                log.info("Fetching current free models from OpenRouter")
                req = Request(
                    f"{OPENROUTER_API_BASE}/models",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://github.com/smart-router",
                        "X-Title": "SmartRouter",
                    },
                )
                with urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())

                free = []
                for model in data.get("data", []):
                    pricing = model.get("pricing", {})
                    prompt_cost = float(pricing.get("prompt", "1") or "1")
                    completion_cost = float(pricing.get("completion", "1") or "1")
                    if prompt_cost == 0 and completion_cost == 0 and is_text_chat_model(model):
                        free.append(model)

                self._models = free
                self._last_fetch = time.time()
                log.info("Found %d free models", len(free))
            except Exception as exc:
                log.warning("Failed to fetch models: %s. Using cached list.", exc)

            return self._models


model_cache = ModelCache()
last_route = {}
last_route_lock = threading.Lock()


def default_config():
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
    return {
        "policy": {"mode": "free-only", "allow_paid_fallback": False},
        "profiles": profiles,
    }


def load_json(path: Path, fallback: dict):
    if not path.exists():
        return dict(fallback)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(fallback)


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_router_config():
    base = default_config()
    current = load_json(CONFIG_FILE, base)
    if not isinstance(current, dict):
        return base
    merged = base
    merged.update({k: v for k, v in current.items() if k != "profiles"})
    current_profiles = current.get("profiles") if isinstance(current.get("profiles"), dict) else {}
    for name, profile in base["profiles"].items():
        custom = current_profiles.get(name) if isinstance(current_profiles, dict) else {}
        if isinstance(custom, dict):
            p = dict(profile)
            p.update(custom)
            merged["profiles"][name] = p
    return merged


def load_cooldowns():
    data = load_json(COOLDOWNS_FILE, {"models": {}, "providers": {}})
    if not isinstance(data, dict):
        return {"models": {}, "providers": {}}
    data.setdefault("models", {})
    data.setdefault("providers", {})
    return data


def load_stats():
    data = load_json(STATS_FILE, {"models": {}, "scenarios": {}})
    if not isinstance(data, dict):
        return {"models": {}, "scenarios": {}}
    data.setdefault("models", {})
    data.setdefault("scenarios", {})
    return data


def is_text_chat_model(model):
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


def _content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
        return " ".join(parts)
    return ""


def _specificity(scenario: str) -> int:
    return 0 if scenario.endswith("_general") else 1


def analyze_scenario(messages):
    text = " ".join(_content_to_text(msg.get("content")) for msg in messages).lower()
    scores = {scenario: 0 for scenario in SCENARIOS}

    for scenario, keywords in SCENARIO_KEYWORDS.items():
        for keyword, weight in keywords.items():
            if keyword in text:
                scores[scenario] += int(weight)

    best = max(SCENARIOS, key=lambda s: (scores[s], _specificity(s)))
    if scores[best] <= 0:
        best = "reasoning_general"

    positive = sorted([(name, value) for name, value in scores.items() if value > 0], key=lambda item: item[1], reverse=True)
    top_score = positive[0][1] if positive else 0
    total = sum(value for _name, value in positive)
    confidence = round((top_score / total), 3) if total > 0 else 0.0

    log.info("Scenario scores: %s; selected=%s", scores, best)
    return {
        "detected_scenario": best,
        "scenario_scores": scores,
        "top_scenarios": positive[:5],
        "scenario_confidence": confidence,
    }


def detect_scenario(messages):
    return analyze_scenario(messages)["detected_scenario"]


def model_supports_tools(model):
    architecture = model.get("architecture") or {}
    supported = [str(x).lower() for x in (architecture.get("supported_parameters") or [])]
    tags = [str(x).lower() for x in (model.get("tags") or [])]
    combined = " ".join([
        str(model.get("id") or "").lower(),
        str(model.get("name") or "").lower(),
        str(model.get("description") or "").lower(),
        " ".join(supported),
        " ".join(tags),
    ])
    markers = ["tool", "tools", "tool_choice", "function", "function_call", "agentic"]
    return any(marker in combined for marker in markers)


def rank_models(models, scenario, tool_request=False, profile=None, cooldowns=None, stats=None):
    def score(model):
        value = 0.0
        model_id = (model.get("id") or "").lower()
        name = (model.get("name") or "").lower()
        desc = (model.get("description") or "").lower()
        ctx = model.get("context_length") or 0
        tags = {tag.lower() for tag in model.get("tags", [])}
        combined = f"{model_id} {name} {desc}"

        if ctx >= 128000:
            value += 30
        elif ctx >= 32000:
            value += 15
        elif ctx >= 8000:
            value += 5

        if scenario.startswith("coding_"):
            if tags & CODING_TAGS:
                value += 40
            if "coder" in combined:
                value += 35
            if "code" in combined:
                value += 30
            if "deepseek" in combined:
                value += 25
            if "qwen" in combined:
                value += 15
            if "instruct" in combined:
                value += 10
            if scenario == "coding_debugging" and ("reason" in combined or "think" in combined):
                value += 12
            if scenario == "coding_architecture" and ctx >= 32000:
                value += 12
            if scenario == "coding_security" and ("guard" in combined or "safe" in combined):
                value += 8
            if scenario == "coding_performance" and ("fast" in combined or "flash" in combined):
                value += 8
        elif scenario.startswith("reasoning_"):
            if tags & REASONING_TAGS:
                value += 40
            if "reasoning" in combined:
                value += 35
            if "think" in combined:
                value += 30
            if "r1" in combined:
                value += 25
            if "qwq" in combined:
                value += 25
            if "gemini" in combined:
                value += 20
            if scenario == "reasoning_math" and "math" in combined:
                value += 12
        elif scenario.startswith("writing_"):
            if tags & WRITING_TAGS:
                value += 40
            if "creative" in combined:
                value += 30
            if "gemini" in combined:
                value += 25
            if "llama" in combined:
                value += 20
            if "mistral" in combined:
                value += 15
            if "chat" in combined:
                value += 10
        elif scenario.startswith("research_"):
            if "flash" in combined or "mini" in combined:
                value += 15
            if "search" in combined:
                value += 10
        elif scenario.startswith("creative_"):
            if "creative" in combined or "story" in combined:
                value += 18
            if "chat" in combined:
                value += 8
        elif scenario == "long_context":
            if ctx >= 128000:
                value += 20
        elif scenario == "vision":
            if "vision" in combined or "image" in combined:
                value += 20
        elif scenario == "fast":
            if any(x in combined for x in ["flash", "mini", "small", "3b", "4b", "7b", "8b"]):
                value += 20

        if tool_request:
            if model_supports_tools(model):
                value += 35
            else:
                value -= 15

        if profile:
            preferred = [str(x) for x in profile.get("preferred", [])]
            if model.get("id") in preferred:
                idx = preferred.index(model.get("id"))
                value += max(20, 60 - idx * 10)

            for p in profile.get("prefer_patterns", []):
                if str(p).lower() in combined:
                    value += 8
            for p in profile.get("avoid_patterns", []):
                if str(p).lower() in combined:
                    value -= 20

            min_context = int(profile.get("min_context") or 0)
            if min_context and ctx < min_context:
                value -= 25

        if cooldowns:
            model_cd = cooldowns.get("models", {}).get(model.get("id"), {})
            until = float(model_cd.get("until", 0) or 0)
            if until > time.time():
                value -= 1000

        if stats:
            model_stats = stats.get("models", {}).get(model.get("id"), {})
            successes = float(model_stats.get("successes", 0) or 0)
            failures = float(model_stats.get("failures", 0) or 0)
            total = successes + failures
            if total > 0:
                success_rate = successes / total
                value += (success_rate - 0.5) * 30
            avg_latency = float(model_stats.get("avg_latency_ms", 0) or 0)
            if avg_latency > 0:
                value -= min(20, avg_latency / 2000)
            last_provider = str(model_stats.get("last_provider", "") or "")
            if last_provider:
                provider_cd = (cooldowns or {}).get("providers", {}).get(last_provider, {})
                provider_until = float(provider_cd.get("until", 0) or 0)
                if provider_until > time.time():
                    value -= 300

        if "2025" in combined:
            value += 10
        elif "2024" in combined:
            value += 5

        if "mini" in combined and "qwen" not in combined:
            value -= 5
        if "tiny" in combined:
            value -= 10

        return value

    ranked = sorted(models, key=score, reverse=True)
    log.info(
        "Top models for [%s] tool_request=%s: %s",
        scenario,
        tool_request,
        [(m.get("id"), round(score(m), 1)) for m in ranked[:5]],
    )
    return ranked


def choose_fast_model(ranked_models):
    fast_markers = ["flash", "mini", "small", "fast", "haiku", "3b", "7b", "8b"]
    for model in ranked_models:
        model_id = str(model.get("id") or "").lower()
        if any(marker in model_id for marker in fast_markers):
            return model.get("id")
    return ranked_models[0].get("id") if ranked_models else None


def select_candidates(ranked_models, free_models, requested_model_raw):
    ranked_ids = [m.get("id") for m in ranked_models if m.get("id")]
    requested = requested_model_raw.strip()
    requested_lower = requested.lower()

    if not requested:
        return ranked_ids, "free-ranked", False, "empty-request"
    if requested_lower.startswith("smart-router/"):
        return ranked_ids, "free-ranked", False, "smart-router-placeholder"

    free_ids = {str(m.get("id") or "") for m in free_models}
    if requested in free_ids:
        ordered = [requested] + [model_id for model_id in ranked_ids if model_id != requested]
        return ordered, "client-free-first", True, "free-model-first"

    return ranked_ids, "client-nonfree-skipped", False, "not-free-or-not-found"


def parse_error_details(body_bytes):
    details = {"message": "", "provider": ""}
    try:
        payload = json.loads((body_bytes or b"").decode("utf-8", errors="ignore"))
        err = payload.get("error", {}) if isinstance(payload, dict) else {}
        details["message"] = str(err.get("message") or "")
        metadata = err.get("metadata", {}) if isinstance(err, dict) else {}
        details["provider"] = str(metadata.get("provider_name") or "")
        raw = str(metadata.get("raw") or "")
        if raw and not details["message"]:
            details["message"] = raw
    except Exception:
        pass
    return details


def should_retry(status, body_bytes):
    if status in {429, 503}:
        return True
    details = parse_error_details(body_bytes)
    combined = f"{details.get('message', '')}".lower()

    if status == 404:
        tool_markers = [
            "no endpoints found",
            "support tool use",
            "tool use",
            "tools",
            "agent",
        ]
        return any(marker in combined for marker in tool_markers)

    if status != 402:
        return False

    retry_markers = [
        "spend limit exceeded",
        "quota",
        "rate limit",
        "provider returned error",
        "credits",
        "payment required",
    ]
    return any(marker in combined for marker in retry_markers)


def cooldown_seconds_for_error(status, message):
    text = str(message or "").lower()
    if "free-models-per-day" in text:
        return 24 * 3600
    if status == 429:
        return 30 * 60
    if status == 402:
        return 6 * 3600
    if status == 503:
        return 15 * 60
    if status == 404 and ("tool use" in text or "no endpoints found" in text):
        return 24 * 3600
    return 10 * 60


def update_stats(model_id, success, latency_ms, status, provider="", scenario=""):
    stats = load_stats()
    models = stats.setdefault("models", {})
    item = models.setdefault(model_id, {"successes": 0, "failures": 0, "avg_latency_ms": 0, "last_status": 0})
    if success:
        item["successes"] = int(item.get("successes", 0)) + 1
    else:
        item["failures"] = int(item.get("failures", 0)) + 1

    current_avg = float(item.get("avg_latency_ms", 0) or 0)
    total = int(item.get("successes", 0)) + int(item.get("failures", 0))
    if total <= 1:
        item["avg_latency_ms"] = int(latency_ms)
    else:
        item["avg_latency_ms"] = int(((current_avg * (total - 1)) + latency_ms) / total)
    item["last_status"] = int(status or 0)
    if provider:
        item["last_provider"] = provider
    item["last_updated_at"] = datetime.now(timezone.utc).isoformat()

    if scenario:
        scenarios = stats.setdefault("scenarios", {})
        scen = scenarios.setdefault(
            scenario,
            {"requests": 0, "successes": 0, "failures": 0, "avg_latency_ms": 0, "last_status": 0, "last_model": ""},
        )
        scen["requests"] = int(scen.get("requests", 0)) + 1
        if success:
            scen["successes"] = int(scen.get("successes", 0)) + 1
        else:
            scen["failures"] = int(scen.get("failures", 0)) + 1
        scen_current_avg = float(scen.get("avg_latency_ms", 0) or 0)
        scen_total = int(scen.get("requests", 0))
        if scen_total <= 1:
            scen["avg_latency_ms"] = int(latency_ms)
        else:
            scen["avg_latency_ms"] = int(((scen_current_avg * (scen_total - 1)) + latency_ms) / scen_total)
        scen["last_status"] = int(status or 0)
        scen["last_model"] = model_id
        scen["last_updated_at"] = datetime.now(timezone.utc).isoformat()

    save_json(STATS_FILE, stats)


def add_cooldown(model_id, provider, status, reason):
    cooldowns = load_cooldowns()
    seconds = cooldown_seconds_for_error(status, reason)
    until = int(time.time() + seconds)
    cooldowns.setdefault("models", {})[model_id] = {
        "until": until,
        "reason": reason,
        "status": status,
        "provider": provider,
    }
    if provider:
        cooldowns.setdefault("providers", {})[provider] = {
            "until": until,
            "reason": reason,
            "status": status,
        }
    save_json(COOLDOWNS_FILE, cooldowns)
    return {
        "model": model_id,
        "provider": provider,
        "status": status,
        "reason": reason,
        "until": until,
        "duration_seconds": seconds,
    }


def normalize_openrouter_url(path):
    if path.startswith("/api/v1/") or path == "/api/v1":
        return f"{OPENROUTER_ORIGIN}{path}"
    if path.startswith("/v1/") or path == "/v1":
        return f"{OPENROUTER_ORIGIN}/api{path}"
    return f"{OPENROUTER_API_BASE}{path if path.startswith('/') else '/' + path}"


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, _format, *args):
        return

    def _api_key(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return os.environ.get("OPENROUTER_API_KEY", "")

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._error(400, "Invalid Content-Length")
            return None
        if length < 0:
            self._error(400, "Invalid Content-Length")
            return None
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._error(400, "Request body must be valid JSON")
            return None
        if not isinstance(payload, dict):
            self._error(400, "Request body must be a JSON object")
            return None
        return payload

    def do_POST(self):
        api_key = self._api_key()
        if not api_key:
            self._error(401, "No API key. Set OPENROUTER_API_KEY in ~/.zshrc")
            return

        body = self._read_json_body()
        if body is None:
            return
        accept_header = (self.headers.get("Accept") or "").lower()
        stream_requested = bool(body.get("stream")) or "text/event-stream" in accept_header
        messages = body.get("messages", [])
        if not isinstance(messages, list):
            self._error(400, "messages must be a list")
            return
        scenario_analysis = analyze_scenario(messages)
        scenario = scenario_analysis["detected_scenario"]
        free_models = model_cache.get_free_models(api_key)

        if not free_models:
            self._error(503, "Could not fetch free models from OpenRouter")
            return

        tool_request = bool(body.get("tools") or body.get("tool_choice") or body.get("parallel_tool_calls"))
        if "beta=true" in self.path.lower():
            tool_request = True

        router_config = load_router_config()
        cooldowns = load_cooldowns()
        stats = load_stats()
        profile_key = scenario
        profile = (router_config.get("profiles") or {}).get(profile_key, {})

        ranked_models = rank_models(
            free_models,
            scenario,
            tool_request=tool_request,
            profile=profile,
            cooldowns=cooldowns,
            stats=stats,
        )
        requested_model_raw = str(body.get("model") or "")
        candidates, routing_tier, requested_model_allowed, requested_model_reason = select_candidates(
            ranked_models,
            free_models,
            requested_model_raw,
        )
        candidates = [c for c in candidates if c]

        if not candidates:
            self._error(503, "Could not choose a model from free model list")
            return
        target_url = normalize_openrouter_url(self.path)
        failed_models = []
        cooldowns_added = []
        final_status = None
        final_body = b""
        final_content_type = "application/json"
        final_model = ""
        final_latency_ms = None
        streamed = False

        for index, chosen in enumerate(candidates):
            attempt_started = time.time()
            attempt_body = dict(body)
            attempt_body["model"] = chosen
            attempt_body.pop("anthropic_version", None)
            if stream_requested:
                attempt_body["stream"] = True

            log.info(
                "Routing %s to %s via model=%s scenario=%s tier=%s requested=%s attempt=%d/%d",
                self.path,
                target_url,
                chosen,
                scenario,
                routing_tier,
                requested_model_raw or "(none)",
                index + 1,
                len(candidates),
            )

            req = Request(
                target_url,
                data=json.dumps(attempt_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://github.com/smart-router",
                    "X-Title": f"SmartRouter/{scenario}",
                },
                method="POST",
            )

            try:
                with urlopen(req, timeout=120) as resp:
                    final_status = resp.status
                    final_content_type = resp.headers.get("Content-Type", "application/json")
                    final_model = chosen
                    latency_ms = int((time.time() - attempt_started) * 1000)
                    final_latency_ms = latency_ms
                    update_stats(chosen, True, latency_ms, final_status, scenario=scenario)
                    if stream_requested:
                        self._proxy_stream(
                            resp,
                            final_status,
                            final_content_type,
                            model=final_model,
                            scenario=scenario,
                            retry_count=len(failed_models),
                        )
                        streamed = True
                        final_body = b""
                        break
                    final_body = resp.read()
                break
            except HTTPError as exc:
                err_body = exc.read()
                err_status = exc.code
                err_details = parse_error_details(err_body)
                failed_models.append({
                    "model": chosen,
                    "status": err_status,
                    "reason": err_details.get("message", "")[:300],
                    "provider": err_details.get("provider", ""),
                })
                latency_ms = int((time.time() - attempt_started) * 1000)
                final_latency_ms = latency_ms
                provider_name = err_details.get("provider", "")
                update_stats(chosen, False, latency_ms, err_status, provider_name, scenario=scenario)
                cooldowns_added.append(
                    add_cooldown(chosen, provider_name, err_status, err_details.get("message", "")[:300])
                )
                log.warning(
                    "Model failed model=%s status=%s provider=%s reason=%s",
                    chosen,
                    err_status,
                    err_details.get("provider", ""),
                    err_details.get("message", "")[:300],
                )

                if should_retry(err_status, err_body) and index < len(candidates) - 1:
                    continue

                final_status = err_status
                final_body = err_body
                final_content_type = exc.headers.get("Content-Type", "application/json") if exc.headers else "application/json"
                final_model = chosen
                break
            except URLError as exc:
                failed_models.append({
                    "model": chosen,
                    "status": 502,
                    "reason": str(exc),
                    "provider": "",
                })
                latency_ms = int((time.time() - attempt_started) * 1000)
                final_latency_ms = latency_ms
                update_stats(chosen, False, latency_ms, 502, scenario=scenario)
                cooldowns_added.append(add_cooldown(chosen, "", 502, str(exc)))
                log.warning("Model failed model=%s status=502 reason=%s", chosen, str(exc))

                if index < len(candidates) - 1:
                    continue

                self._error(502, str(exc))
                return

        retry_count = len(failed_models)
        success = bool(final_status and 200 <= int(final_status) < 300)

        if not success and tool_request and failed_models:
            final_reason = str(failed_models[-1].get("reason") or "").lower()
            if "tool use" in final_reason or "no endpoints found" in final_reason:
                final_status = 503
                final_body = json.dumps({
                    "error": {
                        "message": "No free OpenRouter model currently available for Claude Code tool use. Free quota/provider limits may be exhausted. Try again later or add OpenRouter credits.",
                        "type": "proxy_error",
                    }
                }).encode("utf-8")
                final_content_type = "application/json"
                success = False

        self._record_last_route(
            requested_model=requested_model_raw or "(none)",
            final_model=final_model,
            scenario=scenario,
            tier=routing_tier,
            retry_count=retry_count,
            failed_models=failed_models,
            status=final_status,
            path=self.path,
            success=success,
            tool_request=tool_request,
            latency_ms=final_latency_ms,
            cooldowns_added=cooldowns_added,
            requested_model_allowed=requested_model_allowed,
            requested_model_reason=requested_model_reason,
            scenario_scores=scenario_analysis["scenario_scores"],
            top_scenarios=scenario_analysis["top_scenarios"],
            scenario_confidence=scenario_analysis["scenario_confidence"],
        )
        if streamed:
            return
        self._proxy_response(
            final_status,
            final_body,
            final_content_type,
            model=final_model,
            scenario=scenario,
            retry_count=retry_count,
        )

    def do_GET(self):
        if self.path == "/status":
            self._status()
            return
        if self.path == "/last":
            self._last()
            return

        api_key = self._api_key()
        if not api_key:
            self._error(401, "No API key. Set OPENROUTER_API_KEY in ~/.zshrc")
            return

        req = Request(
            normalize_openrouter_url(self.path),
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/smart-router",
                "X-Title": "SmartRouter",
            },
        )
        try:
            with urlopen(req, timeout=15) as resp:
                self._proxy_response(resp.status, resp.read(), resp.headers.get("Content-Type"))
        except HTTPError as exc:
            self._proxy_response(exc.code, exc.read(), exc.headers.get("Content-Type"))
        except URLError as exc:
            self._error(502, str(exc))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def _status(self):
        api_key = self._api_key()
        free_models = model_cache.get_cached_models()
        if api_key and not free_models:
            threading.Thread(target=model_cache.get_free_models, args=(api_key,), daemon=True).start()
        top_per_scenario = {}
        router_config = load_router_config()
        cooldowns = load_cooldowns()
        stats = load_stats()
        for scenario in SCENARIOS:
            profile = (router_config.get("profiles") or {}).get(scenario, {})
            top_per_scenario[scenario] = [
                m["id"]
                for m in rank_models(
                    free_models,
                    scenario,
                    tool_request=False,
                    profile=profile,
                    cooldowns=cooldowns,
                    stats=stats,
                )[:3]
            ] if free_models else []

        self._json(200, {
            "status": "running",
            "free_models_cached": len(free_models),
            "cache_age_seconds": int(model_cache.cache_age()) if model_cache.cache_age() >= 0 else None,
            "policy": (router_config.get("policy") or {}).get("mode", "free-only"),
            "config_path": str(CONFIG_FILE),
            "config_updated_at": router_config.get("updated_at"),
            "model_cooldowns_active": len((cooldowns.get("models") or {})),
            "provider_cooldowns_active": len((cooldowns.get("providers") or {})),
            "stats_models_tracked": len((stats.get("models") or {})),
            "stats_scenarios_tracked": len((stats.get("scenarios") or {})),
            "top_per_scenario": top_per_scenario,
            "last_route": self._get_last_route(),
        })

    def _last(self):
        self._json(200, self._get_last_route())

    def _get_last_route(self):
        with last_route_lock:
            return dict(last_route)

    def _record_last_route(self, requested_model, final_model, scenario, tier, retry_count, failed_models, status, path, success, tool_request, latency_ms, cooldowns_added, requested_model_allowed, requested_model_reason, scenario_scores, top_scenarios, scenario_confidence):
        payload = {
            "requested_model": requested_model,
            "requested_model_allowed": requested_model_allowed,
            "requested_model_reason": requested_model_reason,
            "final_model": final_model,
            "scenario": scenario,
            "detected_scenario": scenario,
            "scenario_scores": scenario_scores,
            "top_scenarios": top_scenarios,
            "scenario_confidence": scenario_confidence,
            "tier": tier,
            "retry_count": retry_count,
            "success": success,
            "tool_request": tool_request,
            "latency_ms": latency_ms,
            "cooldowns_added": cooldowns_added,
            "failed_models": failed_models,
            "status": status,
            "path": path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with last_route_lock:
            last_route.clear()
            last_route.update(payload)

    def _proxy_response(self, code, body, content_type=None, model=None, scenario=None, retry_count=0):
        self.send_response(code)
        self.send_header("Content-Type", content_type or "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        if model:
            self.send_header("X-Smart-Router-Model", model)
        if scenario:
            self.send_header("X-Smart-Router-Scenario", scenario)
        self.send_header("X-Smart-Router-Retry-Count", str(retry_count))
        self.end_headers()
        self.wfile.write(body)

    def _proxy_stream(self, resp, code, content_type=None, model=None, scenario=None, retry_count=0):
        self.send_response(code)
        self.send_header("Content-Type", content_type or "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        if model:
            self.send_header("X-Smart-Router-Model", model)
        if scenario:
            self.send_header("X-Smart-Router-Scenario", scenario)
        self.send_header("X-Smart-Router-Retry-Count", str(retry_count))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, message):
        self._json(code, {"error": {"message": message, "type": "proxy_error"}})


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        threading.Thread(target=model_cache.get_free_models, args=(api_key,), daemon=True).start()

    server = HTTPServer((PROXY_HOST, PROXY_PORT), ProxyHandler)
    log.info("Smart Router running on http://%s:%s", PROXY_HOST, PROXY_PORT)
    log.info("Status endpoint: http://%s:%s/status", PROXY_HOST, PROXY_PORT)
    log.info("Logs: %s", LOG_FILE)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Smart Router stopped")


if __name__ == "__main__":
    main()
