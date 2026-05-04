#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLI = ROOT / "bin" / "smart-router"


def detect(prompt: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(CLI), "scenario", prompt, "--top", "3"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    return str(payload.get("detected_scenario", ""))


def main() -> int:
    cases = [
        ("Fix this React component layout bug", {"coding_frontend"}),
        ("Debug this Python traceback and fix exception", {"coding_debugging"}),
        ("Write Docker GitHub Actions deploy workflow", {"coding_devops"}),
        ("Optimize SQL query with index suggestions", {"coding_database", "coding_performance"}),
        ("Explain this probability formula proof", {"reasoning_math"}),
        ("Compare pros and cons of two architectures", {"reasoning_analysis", "reasoning_architecture"}),
        ("Create step by step rollout plan", {"reasoning_planning"}),
        ("Review risks in this proposal", {"reasoning_review"}),
        ("Check policy compliance concerns", {"reasoning_legal_policy"}),
        ("Calculate ROI and budget impact", {"reasoning_finance"}),
        ("Rewrite this email in a professional tone", {"writing_email", "writing_rewrite"}),
        ("Summarize this document into key points", {"writing_summary"}),
        ("Fact check this claim with sources", {"research_fact_check"}),
        ("Write a product landing page marketing hook", {"creative_marketing"}),
    ]

    for prompt, expected in cases:
        got = detect(prompt)
        if got not in expected:
            raise AssertionError(f"Prompt={prompt!r} expected one of {sorted(expected)} got {got!r}")

    print("Scenario detection tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
