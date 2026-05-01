# smart-openrouter-router

[![Quick Start](https://img.shields.io/badge/Quick%20Start-Beginner-brightgreen)](#quick-start-beginner)

Smart local proxy for Claude Code that routes requests to the best available **free** OpenRouter models automatically.

## Quick Start (Beginner)

Install once, then run Claude Code through the router.

```bash
./install.sh
```

```bash
smart-router setup
```

`smart-router setup` verifies the new key before saving it and replaces any previously saved key only after verification succeeds.

Note: the default prompt is hidden (no characters will appear). Paste the key and press Enter.

You can also use one of these:

```bash
smart-router setup --visible
```

```bash
OPENROUTER_API_KEY="sk-or-..." smart-router setup --from-env
```

```bash
claude-free
```

The router starts automatically for this session and stops when Claude exits.

Optional:

```bash
smart-router status
smart-router last
smart-router config refresh
smart-router config view
smart-router models
smart-router cooldowns
smart-router stats
```

Installer/developer verification:

```bash
bash test_install_flow.sh
```

Upgrade helpers:

```bash
smart-router version
smart-router upgrade --check
smart-router upgrade
smart-router upgrade --version v0.3.0
```

`smart-router upgrade --check` exit codes:

- `0`: up to date
- `2`: upgrade available
- `1`: error

Help output notes:

- `smart-router -h` and all subcommand help screens include the shared Notes section.

Upgrades keep your saved API key at `~/.config/smart-openrouter-router/api_key`.
You only need to run `smart-router setup` again if:

- you ran `smart-router reset --all`
- you deleted `~/.config/smart-openrouter-router/`
- you only use `OPENROUTER_API_KEY` in the current shell/session

On upgrade, installer next steps only suggest `smart-router setup` when a saved key is missing.

## Install without git (curl)

Pinned (recommended):

```bash
VER=v0.3.3
curl -fsSL "https://raw.githubusercontent.com/arunnarangali/smart-openrouter-router/$VER/smart-router-install.sh" \
  | SMART_ROUTER_VERSION="$VER" bash
```

Latest (convenience, less reproducible):

```bash
curl -fsSL https://raw.githubusercontent.com/arunnarangali/smart-openrouter-router/main/smart-router-install.sh | SMART_ROUTER_VERSION=latest bash
```

Then:

```bash
smart-router setup
claude-free
```

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

For Claude Code tool/agent requests, it also:

6. Detects tool-style requests (`tools`, `tool_choice`, `parallel_tool_calls`, and Claude `?beta=true` flow)
7. Prefers tool-capable free models during ranking
8. Retries `404` tool-use endpoint errors (for example, `No endpoints found that support tool use`)

## Features

- Automatic scenario-based routing
- Free-model filtering (text-in/text-out chat models)
- Correct path normalization (`/v1/...` -> `/api/v1/...`)
- Automatic fallback/retry across free models
- Tool-request aware fallback for Claude Code agent/tool calls
- Visibility endpoints:
  - `GET /status`
  - `GET /last`
  - `/last` includes `success` and `tool_request`
- Response headers:
  - `X-Smart-Router-Model`
  - `X-Smart-Router-Scenario`
  - `X-Smart-Router-Retry-Count`

## Files

- `smart_router.py` - router server
- `bin/claude-free` - starts router and runs Claude Code
- `bin/smart-router` - setup/status/last/reset CLI
- `install.sh` - installer (puts commands in `~/.local/bin`)
- `legacy/` - legacy files (`smart_router_start.sh`, `test_router.sh`, `zshrc_snippet.sh`)

## Setup (Legacy Manual)

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

- `smart-router setup` - store and verify OpenRouter key
- `smart-router status` - router status
- `smart-router last` - last routed request metadata
- `smart-router models` - show current best live free models by scenario
- `smart-router config path|view|explain|reset|refresh` - config management
- `smart-router cooldowns` / `smart-router cooldowns clear` - inspect or clear cooldowns
- `smart-router stats` / `smart-router stats reset` - inspect or clear model stats
- `smart-router reset` - clear runtime state
- `smart-router reset --all` - uninstall and remove key
- `claude-free` - run Claude Code through the router

### Config Refresh

`smart-router config refresh` fetches live OpenRouter free models and updates preferred
lists for coding, reasoning, writing, and fast profiles in:

- `~/.config/smart-openrouter-router/config.json`

The router still enforces free-only filtering at runtime.

Use `smart-router models` to view current best live free models without modifying config.

### Reset behavior

- `smart-router reset` stops the router and clears runtime state (keeps API key)
- `smart-router reset --all` removes key and installed commands

## Verify

Run installer-flow verification (recommended):

```bash
bash test_install_flow.sh
```

Run full verification for legacy/manual setup:

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

### Claude Code says model may not exist

If Claude Code shows `smart-router/best may not exist`, check `router-last`.

This usually means OpenRouter returned a provider/tool-endpoint error, not that the local virtual model is missing.

The router now retries tool-use endpoint failures automatically, and `/last` shows:

- `tool_request`: whether this was a tool/agent-style request
- `success`: whether routing finally succeeded

### Auth conflict in Claude Code

If you see both `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` set, ensure this line is in your shell setup:

```bash
unset ANTHROPIC_AUTH_TOKEN
```

### `401 User not found` after updating key

If you updated your key but still get `401 User not found`, your shell may still have an old `OPENROUTER_API_KEY`.

`claude-free` now prefers the saved key at `~/.config/smart-openrouter-router/api_key` and prints a warning when env and saved keys differ.

Quick reset for current terminal:

```bash
unset OPENROUTER_API_KEY
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
claude-free
```

### Port already in use

If `8080` is occupied, stop existing process or change `PROXY_PORT` in `smart_router.py` and `smart_router_start.sh`.

## Security

- Never commit real API keys.
- Rotate any key that was exposed in terminal/chat history.

## License

MIT
