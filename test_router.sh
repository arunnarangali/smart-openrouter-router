#!/usr/bin/env bash

# Legacy/manual setup verification script.
# For installer-based verification, use: bash test_install_flow.sh

PROXY="http://127.0.0.1:8080"
PASS=0
FAIL=0
WARN=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

pass() { printf "  ${GREEN}PASS${NC}  %s\n" "$1"; PASS=$((PASS + 1)); }
fail() { printf "  ${RED}FAIL${NC}  %s\n" "$1"; FAIL=$((FAIL + 1)); }
warn() { printf "  ${YELLOW}WARN${NC}  %s\n" "$1"; WARN=$((WARN + 1)); }
info() { printf "  ${BLUE}INFO${NC}  %s\n" "$1"; }
section() {
  printf "\n${BOLD}%s${NC}\n" "$1"
  printf "${DIM}%s${NC}\n" "--------------------------------------------------"
}

get_listener_pid() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i :8080 -sTCP:LISTEN -t 2>/dev/null | sed -n '1p'
    return
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp 2>/dev/null | awk '/127.0.0.1:8080|\*:8080/ {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sed -n '1p'
    return
  fi
  printf ""
}

is_placeholder_key() {
  [ "$OPENROUTER_API_KEY" = "YOUR_NEW_KEY_HERE" ]
}

printf "\n${BOLD}Smart Router Verification${NC}\n"

section "LAYER 1 - Environment Variables"

if [ -n "$OPENROUTER_API_KEY" ] && ! is_placeholder_key; then
  prefix=$(printf "%s" "$OPENROUTER_API_KEY" | cut -c1-12)
  pass "OPENROUTER_API_KEY is set (${prefix}...)"
elif is_placeholder_key; then
  fail "OPENROUTER_API_KEY is placeholder (YOUR_NEW_KEY_HERE). Set real rotated key in ~/.zshrc"
else
  fail "OPENROUTER_API_KEY is not set"
fi

if [ "$ANTHROPIC_API_KEY" = "$OPENROUTER_API_KEY" ] && [ -n "$ANTHROPIC_API_KEY" ]; then
  pass "ANTHROPIC_API_KEY matches OPENROUTER_API_KEY"
else
  fail "ANTHROPIC_API_KEY mismatch; should equal OPENROUTER_API_KEY"
fi

if [ "$ANTHROPIC_BASE_URL" = "http://127.0.0.1:8080" ]; then
  pass "ANTHROPIC_BASE_URL points to local proxy"
else
  fail "ANTHROPIC_BASE_URL is '$ANTHROPIC_BASE_URL'; expected http://127.0.0.1:8080"
fi

fresh_auth_token=$(zsh -ic 'printf "%s" "$ANTHROPIC_AUTH_TOKEN"' 2>/dev/null)
if [ -z "$fresh_auth_token" ]; then
  pass "ANTHROPIC_AUTH_TOKEN not set in fresh zsh shell"
else
  warn "ANTHROPIC_AUTH_TOKEN still set in fresh zsh shell (unused by Claude Code)"
fi

for var_name in ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL ANTHROPIC_DEFAULT_HAIKU_MODEL; do
  value="${!var_name}"
  if [ -z "$value" ]; then
    warn "$var_name is empty"
  elif printf "%s" "$value" | grep -q '^smart-router/'; then
    pass "$var_name = $value"
  else
    warn "$var_name = $value (hardcoded real model)"
  fi
done

section "LAYER 2 - Proxy Process"

pid=$(get_listener_pid)
if [ -n "$pid" ]; then
  pass "Proxy is listening on port 8080 (PID $pid)"
else
  fail "Proxy is not listening on port 8080"
fi

if [ -f "$HOME/.smart_router.pid" ]; then
  stored_pid=$(cat "$HOME/.smart_router.pid")
  if kill -0 "$stored_pid" 2>/dev/null; then
    pass "PID file exists and process $stored_pid is alive"
  else
    warn "PID file has stale PID $stored_pid"
  fi
else
  warn "PID file ~/.smart_router.pid not found"
fi

if [ -f "$HOME/.smart_router.log" ]; then
  line_count=$(python3 - <<'PY'
import os
path = os.path.expanduser('~/.smart_router.log')
count = 0
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for count, _ in enumerate(f, start=1):
        pass
print(count)
PY
)
  pass "Log file exists (~/.smart_router.log, ${line_count} lines)"
else
  warn "Log file ~/.smart_router.log not found"
fi

section "LAYER 3 - Proxy Health Check"

status_resp=$(curl -s --max-time 6 "$PROXY/status" 2>/dev/null)
if [ -n "$status_resp" ] && printf "%s" "$status_resp" | python3 -c "import json,sys; json.load(sys.stdin)" >/dev/null 2>&1; then
  pass "/status endpoint responded with JSON"

  cached=$(printf "%s" "$status_resp" | python3 -c "import json,sys; print(int(json.load(sys.stdin).get('free_models_cached',0)))" 2>/dev/null)
  if [ "${cached:-0}" -gt 0 ]; then
    pass "$cached free models cached"
  else
    warn "No free models cached yet"
  fi

  age=$(printf "%s" "$status_resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cache_age_seconds'))" 2>/dev/null)
  if [ "$age" = "None" ] || [ -z "$age" ]; then
    warn "Cache age unavailable"
  elif [ "$age" -lt 1800 ]; then
    pass "Model cache is fresh (${age}s old)"
  else
    warn "Model cache is stale (${age}s old)"
  fi

  info "Top per scenario:"
  STATUS_JSON="$status_resp" python3 - <<'PY'
import json
import os

d = json.loads(os.environ.get("STATUS_JSON", "{}"))
for sc, models in d.get("top_per_scenario", {}).items():
    top = models[0] if models else "none"
    print(f"    {sc:10s} -> {top}")
PY

  has_last_route=$(STATUS_JSON="$status_resp" python3 - <<'PY'
import json
import os
d = json.loads(os.environ.get("STATUS_JSON", "{}"))
print("1" if isinstance(d.get("last_route"), dict) else "0")
PY
)
  if [ "$has_last_route" = "1" ]; then
    pass "/status includes last_route object"
  else
    warn "/status missing last_route object"
  fi
else
  fail "/status endpoint did not return valid JSON"
fi

section "LAYER 4 - OpenRouter API Connectivity"

if [ -z "$OPENROUTER_API_KEY" ] || is_placeholder_key; then
  warn "Skipping OpenRouter API test: key not configured"
else
  or_resp=$(curl -s --max-time 10 -H "Authorization: Bearer $OPENROUTER_API_KEY" "https://openrouter.ai/api/v1/models" 2>/dev/null)
  if printf "%s" "$or_resp" | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'data' in d" >/dev/null 2>&1; then
    total=$(printf "%s" "$or_resp" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['data']))" 2>/dev/null)
    free=$(printf "%s" "$or_resp" | python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(sum(1 for m in d if float((m.get('pricing',{}).get('prompt','1') or '1'))==0 and float((m.get('pricing',{}).get('completion','1') or '1'))==0))" 2>/dev/null)
    pass "OpenRouter API reachable ($total total models, $free free)"
  else
    fail "OpenRouter API call failed; check key validity"
  fi
fi

section "LAYER 5 - Live Routing"

run_scenario_test() {
  scenario="$1"
  prompt="$2"
  tier="$3"
  hdr_file=$(mktemp)
  body_file=$(mktemp)

  curl -s --max-time 40 -D "$hdr_file" -o "$body_file" \
    -X POST "$PROXY/v1/messages" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
    -d "{\"model\":\"$tier\",\"max_tokens\":30,\"messages\":[{\"role\":\"user\",\"content\":\"$prompt\"}]}" >/dev/null

  model=$(python3 - "$hdr_file" <<'PY'
import sys
path = sys.argv[1]
chosen = ""
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.lower().startswith('x-smart-router-model:'):
            chosen = line.split(':', 1)[1].strip()
            break
print(chosen)
PY
)

  retry_count=$(python3 - "$hdr_file" <<'PY'
import sys
path = sys.argv[1]
value = ""
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.lower().startswith('x-smart-router-retry-count:'):
            value = line.split(':', 1)[1].strip()
            break
print(value)
PY
)

  payload_ok=$(python3 - "$body_file" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    data = json.load(f)
ok = isinstance(data, dict) and (('content' in data) or ('choices' in data) or ('error' in data))
print('1' if ok else '0')
PY
)

  if [ "$payload_ok" = "1" ]; then
    if [ -n "$model" ]; then
      pass "[$scenario] Response received; routed model: $model"
    else
      warn "[$scenario] Response received, but no X-Smart-Router-Model header"
    fi

    if [ -n "$retry_count" ] && printf "%s" "$retry_count" | grep -Eq '^[0-9]+$'; then
      pass "[$scenario] Retry header present (count=$retry_count)"
    else
      warn "[$scenario] Missing/invalid X-Smart-Router-Retry-Count header"
    fi
  else
    fail "[$scenario] Invalid response payload"
  fi

  rm -f "$hdr_file" "$body_file"
}

if [ -n "$pid" ] && [ -n "$OPENROUTER_API_KEY" ] && ! is_placeholder_key; then
  info "Running three live prompts through proxy"
  run_scenario_test "coding" "Write a Python function to reverse a string" "smart-router/best"
  run_scenario_test "reasoning" "Analyze the trade-offs between REST and GraphQL APIs" "smart-router/best"
  run_scenario_test "writing" "Write a short blog post intro about AI trends" "smart-router/fast"
else
  warn "Skipping live routing tests: proxy not ready or key not configured"
fi

section "LAYER 6 - Last Route Visibility"

last_resp=$(curl -s --max-time 6 "$PROXY/last" 2>/dev/null)
if [ -n "$last_resp" ] && printf "%s" "$last_resp" | python3 -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d, dict)" >/dev/null 2>&1; then
  required_ok=$(printf "%s" "$last_resp" | python3 -c "import json,sys; d=json.load(sys.stdin); req=['requested_model','final_model','scenario','tier','retry_count','success','tool_request','latency_ms','cooldowns_added','failed_models','status','timestamp']; print('1' if all(k in d for k in req) else '0')")
  if [ "$required_ok" = "1" ]; then
    pass "/last endpoint returns full routing metadata"
    info "Last route snapshot:"
    LAST_JSON="$last_resp" python3 - <<'PY'
import json
import os
d = json.loads(os.environ.get("LAST_JSON", "{}"))
print(f"    requested: {d.get('requested_model')}")
print(f"    final:     {d.get('final_model')}")
print(f"    scenario:  {d.get('scenario')}  tier: {d.get('tier')}  retries: {d.get('retry_count')}")
print(f"    success:   {d.get('success')}  tool_request: {d.get('tool_request')}")
print(f"    latency:   {d.get('latency_ms')} ms  cooldowns_added: {len(d.get('cooldowns_added', []))}")
PY
  else
    fail "/last endpoint missing required keys"
  fi
else
  fail "/last endpoint did not return valid JSON"
fi

section "LAYER 7 - Log Sanity"

if [ -f "$HOME/.smart_router.log" ]; then
  errors=$(python3 - <<'PY'
import os
path = os.path.expanduser('~/.smart_router.log')
count = 0
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        u = line.upper()
        if 'ERROR' in u or 'CRITICAL' in u:
            count += 1
print(count)
PY
)
  routes=$(python3 - <<'PY'
import os
path = os.path.expanduser('~/.smart_router.log')
count = 0
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if ' via model=' in line and ' scenario=' in line:
            count += 1
print(count)
PY
)

  if [ "$errors" -eq 0 ]; then
    pass "No ERROR/CRITICAL entries in router log"
  else
    warn "$errors error entries found in router log"
  fi

  if [ "$routes" -gt 0 ]; then
    pass "$routes routing decision(s) recorded"
    info "Last 3 routing entries:"
    python3 - <<'PY'
import os
path = os.path.expanduser('~/.smart_router.log')
hits = []
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if ' via model=' in line and ' scenario=' in line:
            hits.append(line.rstrip())
for line in hits[-3:]:
    print(f"    {line}")
PY
  else
    warn "No routing entries found yet"
  fi
else
  warn "Log file missing; cannot run log sanity checks"
fi

section "SUMMARY"

printf "  Passed: %s\n" "$PASS"
printf "  Failed: %s\n" "$FAIL"
printf "  Warned: %s\n" "$WARN"

if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  printf "\n${GREEN}Everything is working perfectly.${NC}\n"
elif [ "$FAIL" -eq 0 ]; then
  printf "\n${YELLOW}Almost there. Review warnings above.${NC}\n"
else
  printf "\n${RED}Fix failures above before relying on routing.${NC}\n"
fi
