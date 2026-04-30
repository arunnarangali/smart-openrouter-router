# OpenRouter + Claude Code - Smart Router Setup

export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"
unset ANTHROPIC_AUTH_TOKEN
export ANTHROPIC_API_KEY="$OPENROUTER_API_KEY"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8080"

export ANTHROPIC_DEFAULT_OPUS_MODEL="smart-router/best"
export ANTHROPIC_DEFAULT_SONNET_MODEL="smart-router/best"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="smart-router/fast"

if [ -f "$HOME/smart_router_start.sh" ]; then
    bash "$HOME/smart_router_start.sh" 2>/dev/null
fi

alias router-status='echo "\n=== Smart Router Status ===" && curl -s http://127.0.0.1:8080/status | python3 -m json.tool'
alias router-last='curl -s http://127.0.0.1:8080/last | python3 -m json.tool'
alias router-logs='echo "Tailing Smart Router logs (Ctrl+C to stop):" && tail -f ~/.smart_router.log'
alias router-stop='if [ -f ~/.smart_router.pid ]; then kill $(cat ~/.smart_router.pid) 2>/dev/null && rm ~/.smart_router.pid && echo "Router stopped"; else echo "Router not running"; fi'
alias router-restart='router-stop; sleep 1; bash ~/smart_router_start.sh'
alias router-models='curl -s http://127.0.0.1:8080/status | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"Free models available: {d.get(\\\"free_models_cached\\\")}\"); [print(f\"  {sc:12s}: {models[0] if models else \\\"n/a\\\"}\") for sc,models in d.get(\\\"top_per_scenario\\\",{}).items()]"'
