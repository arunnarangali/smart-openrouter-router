# smart-openrouter-router

Smart local proxy for Claude Code that routes requests to the best available **free** OpenRouter models automatically.

## Full Documentation

For complete step-by-step setup, prerequisites, troubleshooting, and operations, read:

- [FULL_GUIDE.md](./FULL_GUIDE.md)

## How it works

Claude Code sends requests to `ANTHROPIC_BASE_URL`.

This router sits in the middle:

`Claude Code -> localhost:8080 -> OpenRouter`

For each request, it:

1. Detects scenario from prompt (`coding`, `reasoning`, `writing`)
2. Fetches free models from OpenRouter (`/api/v1/models`) with cache
3. Ranks models by scenario
4. Routes to a best candidate
5. If provider/model fails (`402`, `429`, `503`, quota/spend/rate errors), retries next ranked model automatically

## Features

- Automatic scenario-based routing
- Free-model filtering (text-in/text-out chat models)
- Correct path normalization (`/v1/...` -> `/api/v1/...`)
- Automatic fallback/retry across free models
- Visibility endpoints:
  - `GET /status`
  - `GET /last`
- Response headers:
  - `X-Smart-Router-Model`
  - `X-Smart-Router-Scenario`
  - `X-Smart-Router-Retry-Count`

## Files

- `smart_router.py` - router server
- `smart_router_start.sh` - auto-start helper
- `test_router.sh` - verification suite
- `zshrc_snippet.sh` - shell setup block

## Setup

1. Copy files to your home directory:

```bash
cp smart_router.py ~/smart_router.py
cp smart_router_start.sh ~/smart_router_start.sh
cp test_router.sh ~/test_router.sh
chmod +x ~/smart_router_start.sh ~/test_router.sh
```

2. Add `zshrc_snippet.sh` contents to your `~/.zshrc`.

3. Set your OpenRouter key in that block:

```bash
export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"
```

4. Reload shell:

```bash
source ~/.zshrc
```

## Commands

- `router-status` - router status and top models
- `router-last` - last routed request metadata
- `router-logs` - tail router logs
- `router-stop` - stop router
- `router-restart` - restart router
- `router-models` - one-line top models summary

## Verify

Run full verification:

```bash
bash ~/test_router.sh
```

## Troubleshooting

### 402 provider spend-limit/quota errors

This can happen on specific OpenRouter providers even for `:free` models.

The router now retries next ranked free models automatically. Check fallback chain with:

```bash
router-last
```

### Auth conflict in Claude Code

If you see both `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` set, ensure this line is in your shell setup:

```bash
unset ANTHROPIC_AUTH_TOKEN
```

### Port already in use

If `8080` is occupied, stop existing process or change `PROXY_PORT` in `smart_router.py` and `smart_router_start.sh`.

## Security

- Never commit real API keys.
- Rotate any key that was exposed in terminal/chat history.

## License

MIT
