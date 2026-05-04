from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_HOST = "127.0.0.1"


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((DEFAULT_HOST, 0))
        return int(sock.getsockname()[1])


def _json_request(url: str, payload: dict[str, Any] | None = None, method: str = "GET", timeout: float = 30.0) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw or b"{}")


def _resolve_router_script() -> Path:
    pkg_root = Path(__file__).resolve().parent.parent
    local = pkg_root / "smart_router.py"
    if local.exists():
        return local
    installed = Path(sys.prefix) / "share" / "smart-openrouter-router" / "smart_router.py"
    if installed.exists():
        return installed
    raise FileNotFoundError("smart_router.py not found for SDK runtime")


class SmartRouter:
    def __init__(self, api_key: str | None = None, host: str = DEFAULT_HOST, port: int = 0, auto_start: bool = True):
        self.api_key = (api_key or os.environ.get("OPENROUTER_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required (argument or environment variable)")
        self.host = host
        self.port = int(port or 0)
        self.auto_start = bool(auto_start)
        self._proc: subprocess.Popen | None = None

    @property
    def base_url(self) -> str:
        if not self.port:
            raise RuntimeError("Router is not started")
        return f"http://{self.host}:{self.port}"

    def start(self) -> "SmartRouter":
        if self._proc and self._proc.poll() is None:
            return self
        if not self.port:
            self.port = _pick_free_port()
        script = _resolve_router_script()
        env = os.environ.copy()
        env["OPENROUTER_API_KEY"] = self.api_key
        env["PROXY_PORT"] = str(self.port)
        self._proc = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        self._wait_for_status()
        return self

    def _wait_for_status(self, timeout: float = 8.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.status()
                return
            except Exception:
                time.sleep(0.2)
        self.stop()
        raise RuntimeError("Smart Router failed to start")

    def stop(self) -> None:
        if not self._proc:
            return
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=2)
        self._proc = None

    def ensure_started(self) -> None:
        if self._proc and self._proc.poll() is None:
            return
        if not self.auto_start:
            raise RuntimeError("Router is not running. Call start() first.")
        self.start()

    def status(self) -> dict[str, Any]:
        self.ensure_started()
        return _json_request(f"{self.base_url}/status")

    def last(self) -> dict[str, Any]:
        self.ensure_started()
        return _json_request(f"{self.base_url}/last")

    def route_chat(self, messages: list[dict[str, Any]], scenario: str | None = None, model: str = "smart-router/best", stream: bool = False, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_started()
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": bool(stream),
        }
        if scenario:
            body["metadata"] = {"scenario_hint": scenario}
        if extra:
            body.update(extra)
        try:
            return _json_request(f"{self.base_url}/v1/chat/completions", payload=body, method="POST", timeout=120)
        except HTTPError as exc:
            payload = exc.read()
            try:
                err = json.loads(payload or b"{}")
            except Exception:
                err = {"error": {"message": str(exc)}}
            raise RuntimeError(err.get("error", {}).get("message", str(exc))) from exc
        except URLError as exc:
            raise RuntimeError(str(exc)) from exc

    def get_best_model(self, prompt: str, scenario: str | None = None) -> str:
        self.ensure_started()
        if scenario:
            status = self.status()
            options = (status.get("top_per_scenario") or {}).get(scenario) or []
            return options[0] if options else ""
        preview = self.route_chat(messages=[{"role": "user", "content": prompt}], model="smart-router/fast", extra={"max_tokens": 1})
        return str((preview.get("model") or preview.get("id") or ""))

    def __enter__(self) -> "SmartRouter":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()


def start_router(api_key: str | None = None, port: int = 8080) -> SmartRouter:
    router = SmartRouter(api_key=api_key, port=port, auto_start=True)
    router.start()
    return router


def route_chat(messages: list[dict[str, Any]], scenario: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    with SmartRouter(api_key=api_key, auto_start=True) as router:
        return router.route_chat(messages=messages, scenario=scenario)


def get_best_model(prompt: str, scenario: str | None = None, api_key: str | None = None) -> str:
    with SmartRouter(api_key=api_key, auto_start=True) as router:
        return router.get_best_model(prompt=prompt, scenario=scenario)
