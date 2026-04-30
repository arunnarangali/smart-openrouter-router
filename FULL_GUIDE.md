# Full Guide: Smart OpenRouter Router for Claude Code

This guide is written for someone starting from zero. Follow it step by step and you can set up the smart local router without manual model switching.

---

## 1) What this project does

Normally, Claude Code sends requests directly to the configured API endpoint.

With this project, Claude Code sends to a local proxy first:

`Claude Code -> localhost:8080 -> OpenRouter`

The proxy then:

1. Reads your prompt
2. Detects scenario (`coding`, `reasoning`, `writing`)
3. Fetches current free models from OpenRouter
4. Ranks them for that scenario
5. Sends request to the best free model
6. If provider/model fails (402/429/503), automatically retries the next free model

For Claude Code agent/tool workflows, it also:

7. Detects tool-style requests (`tools`, `tool_choice`, `parallel_tool_calls`, and Claude `?beta=true` request path)
8. Prefers likely tool-capable free models in ranking
9. Retries tool endpoint failures like `404 No endpoints found that support tool use`

You keep using Claude Code normally. Model routing is automatic.

---

## 2) Prerequisites

You need:

- Operating system: Linux or macOS
- Shell: `zsh`
- `python3` (3.9 or newer recommended)
- `curl`
- `git`
- Claude Code installed and working
- OpenRouter account
- OpenRouter API key

Optional but helpful:

- `lsof` or `ss` (for port/process checks)
- `python3 -m json.tool` (pretty JSON output)

Quick check:

```bash
python3 --version
zsh --version
git --version
curl --version
```

---

## 3) Clone the repository

```bash
git clone git@github.com:arunnarangali/smart-openrouter-router.git
cd smart-openrouter-router
```

Repository files:

- `smart_router.py` - main proxy server
- `smart_router_start.sh` - auto-start script
- `test_router.sh` - full verification test
- `zshrc_snippet.sh` - shell setup block
- `README.md` - quick guide
- `FULL_GUIDE.md` - this complete guide

---

## 4) Install router scripts to your home directory

Claude shell config in this project expects scripts in your home folder.

```bash
cp smart_router.py ~/smart_router.py
cp smart_router_start.sh ~/smart_router_start.sh
cp test_router.sh ~/test_router.sh
chmod +x ~/smart_router_start.sh ~/test_router.sh
```

---

## 5) Configure your `.zshrc`

Open your `~/.zshrc` and add the content from `zshrc_snippet.sh`.

Fast way:

```bash
cat zshrc_snippet.sh >> ~/.zshrc
```

Now edit `~/.zshrc` and set your real key:

```bash
export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"
```

### Important variables explained

- `OPENROUTER_API_KEY`:
  - Your OpenRouter key
- `unset ANTHROPIC_AUTH_TOKEN`:
  - Prevents auth conflict in Claude Code
- `ANTHROPIC_API_KEY="$OPENROUTER_API_KEY"`:
  - Claude Code uses this key
- `ANTHROPIC_BASE_URL="http://127.0.0.1:8080"`:
  - Sends Claude Code traffic through local router
- `ANTHROPIC_DEFAULT_*_MODEL="smart-router/..."`:
  - Virtual names that proxy resolves to real models

### Model virtual names

- `smart-router/best`:
  - Highest-ranked free model for detected scenario
- `smart-router/fast`:
  - Faster/smaller model preference, with fallback

---

## 6) Reload shell and start router

```bash
source ~/.zshrc
```

Auto-start should run from `.zshrc`. Check status:

```bash
router-status
```

If needed, start manually:

```bash
bash ~/smart_router_start.sh
```

---

## 7) Verify end-to-end setup

Run the full test suite:

```bash
bash ~/test_router.sh
```

The test validates:

1. Environment variables
2. Proxy process and port
3. `/status` health and model cache
4. OpenRouter API connectivity
5. Live routing for coding/reasoning/writing
6. `/last` metadata visibility
7. Log sanity

---

## 8) How to use with Claude Code

1. Open a fresh terminal
2. Start Claude Code
3. Send prompts as usual

You do not need to manually select real OpenRouter model IDs.

The proxy chooses and retries automatically.

---

## 9) How to see which real model was used

After any Claude Code request:

```bash
router-last
```

This shows fields like:

- `requested_model` (for example, `smart-router/best`)
- `final_model` (actual OpenRouter model used)
- `scenario`
- `tier`
- `retry_count`
- `success` (final request success state)
- `tool_request` (whether request was tool/agent-style)
- `failed_models` (if retries happened)

You can also view status summary:

```bash
router-status
```

And logs:

```bash
router-logs
```

---

## 10) Fallback behavior (why this matters)

Sometimes a `:free` model can still fail on a specific provider (for example quota/spend-limit/rate-limit at that backend).

The router now retries next ranked free models automatically.

It also retries tool-endpoint failures for Claude Code, including:

- `404 No endpoints found that support tool use`
- provider quota/rate/spend failures on intermediate candidates

Example flow:

1. Try `qwen/qwen3-coder:free`
2. Provider fails with 402
3. Retry `qwen/qwen3-next-80b-a3b-instruct:free`
4. If needed, continue down ranked list
5. Return first successful result

This makes Claude Code usage much more reliable.

---

## 11) Helper commands

- `router-status` - show cache and top models
- `router-last` - show last real routed model and retry info
- `router-models` - quick top-model summary
- `router-logs` - stream router logs
- `router-stop` - stop router
- `router-restart` - restart router

---

## 12) Common issues and fixes

### A) `router-last: command not found`

Run:

```bash
source ~/.zshrc
```

Then retry.

### B) Claude Code auth conflict warning

If you see both token and API key warning, ensure this exists in `.zshrc`:

```bash
unset ANTHROPIC_AUTH_TOKEN
```

Then open a fresh terminal.

### C) `402 spend limit exceeded`

This may come from a specific provider backend. Router should fallback automatically now.

Check details:

```bash
router-last
router-logs
```

### G) Claude Code says `smart-router/best` may not exist

This message is often a downstream provider/tool-endpoint failure, not a missing local model name.

Run:

```bash
router-last
```

Check these fields:

- `tool_request`: true means Claude tool/agent request path
- `success`: false means all candidates failed
- `failed_models`: exact provider/model errors during fallback chain

If you see many `free-models-per-day` or provider quota errors, you may need to wait, use another key, or add OpenRouter credits.

### D) Port 8080 already in use

Stop current process or change port in:

- `smart_router.py` (`PROXY_PORT`)
- `smart_router_start.sh` (`PROXY_PORT`)
- `.zshrc` (`ANTHROPIC_BASE_URL`)

### E) `No API key` or OpenRouter auth errors

- Verify `OPENROUTER_API_KEY` in `.zshrc`
- Run `source ~/.zshrc`
- Retry `router-status`

### F) Claude Code still using old settings

- Close Claude Code
- Open a fresh terminal
- Start Claude Code again

---

## 13) Security checklist

- Never commit real API keys
- Use placeholders in shared files
- Rotate any key exposed in chat/history/screenshots
- Keep `.env` and secret files out of git

To rotate OpenRouter key:

1. Open OpenRouter dashboard
2. Delete old key
3. Create new key
4. Update `.zshrc`
5. Run:

```bash
source ~/.zshrc
router-restart
```

---

## 14) Update project later

If repository changes:

```bash
cd ~/smart-openrouter-router
git pull
cp smart_router.py ~/smart_router.py
cp smart_router_start.sh ~/smart_router_start.sh
cp test_router.sh ~/test_router.sh
chmod +x ~/smart_router_start.sh ~/test_router.sh
router-restart
```

---

## 15) Uninstall

1. Remove router block from `~/.zshrc`
2. Remove files:

```bash
rm -f ~/smart_router.py ~/smart_router_start.sh ~/test_router.sh
rm -f ~/.smart_router.pid ~/.smart_router.log
```

3. Reload shell:

```bash
source ~/.zshrc
```

---

## 16) Quick success checklist

- `router-status` returns JSON
- `bash ~/test_router.sh` shows no failures
- Claude Code works with `smart-router/best`
- `router-last` shows final real model and retry count

If all are true, setup is complete.
