#!/usr/bin/env python3
"""Tests for response body model rewrite (Approach A)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from smart_router import _rewrite_json_model, REWRITE_MODEL


def test_json_body_rewrite():
    body = json.dumps({"id": "chatcmpl-xxx", "model": "smart-router/best", "choices": []}).encode()
    rewritten = _rewrite_json_model(body, "qwen/qwen3-coder:free")
    parsed = json.loads(rewritten)
    assert parsed["model"] == "qwen/qwen3-coder:free"
    assert parsed["id"] == "chatcmpl-xxx"


def test_json_body_no_rewrite_on_non_dict():
    body = b"null"
    assert _rewrite_json_model(body, "qwen/qwen3-coder:free") is body


def test_json_body_no_rewrite_on_bad_json():
    body = b"not json"
    assert _rewrite_json_model(body, "qwen/qwen3-coder:free") is body


def test_json_body_no_rewrite_empty():
    assert _rewrite_json_model(b"", "model-x") == b""


def test_json_body_rewrite_empty_model_preserved():
    body = json.dumps({"model": ""}).encode()
    rewritten = _rewrite_json_model(body, "real-model")
    assert json.loads(rewritten)["model"] == "real-model"


def test_sse_single_data_line():
    chunk = b"data: " + json.dumps({"model": "smart-router/best", "choices": []}).encode() + b"\n\n"
    handler = _HandlerStub()
    rewritten = handler._rewrite_sse_chunk(chunk, "qwen/qwen3-coder:free")
    assert rewritten == b"data: " + json.dumps({"model": "qwen/qwen3-coder:free", "choices": []}).encode() + b"\n\n"


def test_sse_multiple_data_lines():
    d1 = json.dumps({"model": "virtual", "c": 1})
    d2 = json.dumps({"model": "virtual", "c": 2})
    chunk = b"data: " + d1.encode() + b"\n\ndata: " + d2.encode() + b"\n\n"
    handler = _HandlerStub()
    rewritten = handler._rewrite_sse_chunk(chunk, "real-model")
    lines = rewritten.split(b"\n")
    for line in lines:
        if line.startswith(b"data: ") and not line.startswith(b"data: [DONE]"):
            parsed = json.loads(line[6:])
            assert parsed["model"] == "real-model"


def test_sse_data_done_not_touched():
    chunk = b"data: [DONE]\n\n"
    handler = _HandlerStub()
    assert handler._rewrite_sse_chunk(chunk, "any") == chunk


def test_sse_chunk_boundary_split():
    """Simulate a JSON object split across two chunks."""
    d = json.dumps({"model": "virtual", "x": "y"})
    mid = len(d) // 2
    chunk1 = b"data: " + d[:mid].encode()
    chunk2 = d[mid:].encode() + b"\n\n"
    handler = _HandlerStub()
    r1 = handler._rewrite_sse_chunk(chunk1, "real-model")
    r2 = handler._rewrite_sse_chunk(chunk2, "real-model")
    assert r1 == b"", f"Expected empty for partial chunk, got {r1}"
    full = b"data: " + json.dumps({"model": "real-model", "x": "y"}).encode() + b"\n\n"
    assert r2 == full, f"Expected {full}, got {r2}"


def test_sse_non_data_line_preserved():
    chunk = b": comment\n\n"
    handler = _HandlerStub()
    assert handler._rewrite_sse_chunk(chunk, "m") == chunk


def test_rewrite_disabled_by_default():
    """Verify REWRITE_MODEL is False when env var is not '1'."""
    assert REWRITE_MODEL is False


class _HandlerStub:
    """Minimal stand-in for ProxyHandler SSE state."""
    MAX_SSE_CARRY = 16384
    _sse_tail = b""

    def _rewrite_sse_chunk(self, chunk, new_model):
        data = (self._sse_tail + chunk) if self._sse_tail else chunk
        if data.endswith(b"\n"):
            self._sse_tail = b""
            return self._rewrite_sse_lines(data, new_model)
        idx = data.rfind(b"\n")
        if idx == -1:
            if len(data) > self.MAX_SSE_CARRY:
                self._sse_tail = b""
                return data
            self._sse_tail = data
            return b""
        self._sse_tail = data[idx + 1:]
        return self._rewrite_sse_lines(data[:idx + 1], new_model)

    @staticmethod
    def _rewrite_sse_lines(data, new_model):
        lines = data.split(b"\n")
        out = []
        for line in lines:
            if line.startswith(b"data: ") and not line.startswith(b"data: [DONE]"):
                try:
                    payload = json.loads(line[6:])
                    if isinstance(payload, dict):
                        payload["model"] = new_model
                        out.append(b"data: " + json.dumps(payload, ensure_ascii=False).encode("utf-8"))
                        continue
                except (json.JSONDecodeError, Exception):
                    pass
            out.append(line)
        return b"\n".join(out)


def main() -> int:
    test_json_body_rewrite()
    test_json_body_no_rewrite_on_non_dict()
    test_json_body_no_rewrite_on_bad_json()
    test_json_body_no_rewrite_empty()
    test_json_body_rewrite_empty_model_preserved()
    test_sse_single_data_line()
    test_sse_multiple_data_lines()
    test_sse_data_done_not_touched()
    test_sse_chunk_boundary_split()
    test_sse_non_data_line_preserved()
    test_rewrite_disabled_by_default()
    print("Response rewrite tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
