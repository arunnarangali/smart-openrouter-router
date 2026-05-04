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
- `smart_router_common.py` - shared scenarios/config/filter helpers
- `bin/claude-free` - starts router and runs Claude Code
- `bin/opencode-free` - starts router and runs OpenCode
- `bin/smart-router` - setup/status/last/reset CLI
- `install.sh` - installer (puts commands in `~/.local/bin`)
- `smart-router-install.sh` - curl-based installer
- `test_install_flow.sh` - installer-flow verification (recommended)
- `legacy/` - legacy files (`smart_router_start.sh`, `test_router.sh`, `zshrc_snippet.sh`)
- `README.md` - quick guide
- `FULL_GUIDE.md` - this complete guide

---

## 4) Install (Beginner - Recommended)

Run the installer (adds commands to `~/.local/bin`):

```bash
./install.sh
```

### Install without git (curl)

Pinned (recommended):

```bash
VER=<release-tag>
curl -fsSL "https://raw.githubusercontent.com/arunnarangali/smart-openrouter-router/$VER/smart-router-install.sh" \
  | SMART_ROUTER_VERSION="$VER" bash
```

### Package artifacts (v0.5.0+)

Tagged GitHub releases also publish package artifacts:

- Python wheel and sdist
- npm tarball (`.tgz`)

This allows pip/npm-style installs from release assets in addition to the curl installer.

---

## SDK Integration (v0.6.0+)

You can now integrate Smart Router into existing projects without re-implementing
scenario detection, ranking, cooldowns, fallback, and stats.

### Python projects

```python
from smart_openrouter_router import SmartRouter

with SmartRouter() as router:
    result = router.route_chat([
        {"role": "user", "content": "Create a Django serializer"}
    ])
    print(result)
```

### Node/Express backends

```js
import express from "express"
import { createSmartRouter } from "smart-openrouter-router"

const app = express()
app.use(express.json())

const router = createSmartRouter({ apiKey: process.env.OPENROUTER_API_KEY })
await router.start()

app.post("/api/chat", async (req, res) => {
  try {
    const out = await router.routeChat({ messages: req.body.messages || [] })
    res.json(out)
  } catch (err) {
    res.status(500).json({ error: String(err) })
  }
})
```

### React safety

- Never put `OPENROUTER_API_KEY` directly in frontend/browser code.
- React app -> your backend API -> Smart Router -> OpenRouter.
- Keep keys on server only.

Latest (convenience, less reproducible):

```bash
curl -fsSL https://raw.githubusercontent.com/arunnarangali/smart-openrouter-router/main/smart-router-install.sh | SMART_ROUTER_VERSION=latest bash
```

Then:

```bash
smart-router setup
claude-free
opencode-free
```

If the installer tells you to add `~/.local/bin` to your PATH, do it now and open a new terminal.

Now set your OpenRouter key:

```bash
smart-router setup
```

`smart-router setup` verifies the new key before saving it and replaces any previously saved key only after verification succeeds.

Note: the default prompt is hidden (no characters will appear). Paste the key and press Enter.

If you prefer visible input:

```bash
smart-router setup --visible
```

If you want a non-interactive setup:

```bash
OPENROUTER_API_KEY="sk-or-..." smart-router setup --from-env
```

Run Claude Code through the router:

```bash
claude-free
opencode-free
```

OpenCode note: dropdown model entries are compatibility placeholders for
OpenCode UI/provider wiring. The router still ignores those client model IDs
and enforces free-only ranked selection at runtime.

The router starts automatically for this session and stops when Claude exits.

Check status and last route:

```bash
smart-router status
smart-router last
smart-router models
smart-router config refresh
smart-router config view
smart-router cooldowns
smart-router stats
```

Config command summary:

```bash
smart-router config path
smart-router config view
smart-router config explain
smart-router config reset
smart-router config refresh
```

- `config refresh` updates preferred model recommendations from live OpenRouter free models.
- Router still enforces free-only filtering at request time.

Check and upgrade versions:

```bash
smart-router version
smart-router upgrade --check
smart-router upgrade
smart-router upgrade --version v0.3.0
```

`smart-router upgrade --check` exit codes:

- `0` up to date
- `2` upgrade available
- `1` error

Help output notes:

- `smart-router -h` and all subcommand help screens include the shared Notes section.
- Help screens also include the `<system-reminder>...</system-reminder>` block.

Upgrades keep your saved API key at `~/.config/smart-openrouter-router/api_key`.
You only need to run `smart-router setup` again if:

- you ran `smart-router reset --all`
- you deleted `~/.config/smart-openrouter-router/`
- you only use `OPENROUTER_API_KEY` in the current shell/session

On upgrade, installer next steps only suggest `smart-router setup` when a saved key is missing.

---

## 5) Install router scripts to your home directory (Legacy)

Claude shell config in this project expects scripts in your home folder.

```bash
cp smart_router.py ~/smart_router.py
cp smart_router_start.sh ~/smart_router_start.sh
cp test_router.sh ~/test_router.sh
chmod +x ~/smart_router_start.sh ~/test_router.sh
```

---

## 6) Configure your `.zshrc` (Legacy)

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

## 7) Reload shell and start router (Legacy)

```bash
source ~/.zshrc
```

Auto-start should run from `.zshrc`. Check status:

```bash
smart-router status
```

If needed, start manually:

```bash
bash ~/smart_router_start.sh
```

---

## 8) Verify end-to-end setup

Run installer-flow verification (recommended):

```bash
bash test_install_flow.sh
```

Run full legacy/manual suite only if you use the legacy `.zshrc` flow:

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

## 9) How to use with Claude Code

1. Open a fresh terminal
2. Start Claude Code
3. Send prompts as usual

You do not need to manually select real OpenRouter model IDs.

The proxy chooses and retries automatically.

---

## 10) How to see which real model was used

After any Claude Code request:

```bash
smart-router last
```

This shows fields like:

- `requested_model` (for example, `smart-router/best`)
- `final_model` (actual OpenRouter model used)
- `scenario`
- `tier`
- `retry_count`
- `success` (final request success state)
- `tool_request` (whether request was tool/agent-style)
- `latency_ms` (request latency for chosen model)
- `cooldowns_added` (cooldowns recorded during fallback)
- `failed_models` (if retries happened)

You can also view status summary:

```bash
smart-router status
```

And logs:

```bash
smart-router logs
```

---

## 11) Fallback behavior (why this matters)

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

## 12) Helper commands

- `smart-router setup` - store and verify OpenRouter key
- `smart-router status` - router status
- `smart-router last` - last routed request metadata
- `smart-router models` - current best live free models by scenario
- `smart-router models --human` - grouped human-readable model summary
- `smart-router scenario "prompt text"` - show detected scenario, score table, and confidence
- `smart-router scenario --explain "prompt text"` - include matched keywords and weighted contributions
- `smart-router scenario --compare prompts.txt` - analyze one prompt per line
- `smart-router config path|view|explain|reset|refresh` - config file management
- `smart-router config get/set/validate/diff-defaults` - advanced config UX helpers
- `smart-router cooldowns` / `smart-router cooldowns clear` - cooldown visibility/control
- `smart-router stats` / `smart-router stats reset` - performance stats visibility/control
- `smart-router logs` - show recent router log lines
- `smart-router doctor` - run environment/runtime health checks
- `smart-router doctor --fix-suggestions` - include suggested remediation steps
- `smart-router reset` - clear runtime state
- `smart-router reset --all` - uninstall and remove key
- `smart-router uninstall` - remove installed commands and local state
- `claude-free` - run Claude Code through the router
- `opencode-free` - run OpenCode through the router

### Streaming behavior

- If the client requests streaming (`stream=true` or `Accept: text/event-stream`), output is forwarded incrementally.
- Retries only occur before streaming starts; the router cannot switch models mid-stream.

### Client model behavior

- If client sends an explicit model ID, router checks live free models first.
- It is used first only when it is an exact free-model match.
- Paid/non-free/not-found IDs are skipped, then router continues with ranked free fallback models.

### Reset behavior

- `smart-router reset` stops the router and clears runtime state (keeps API key)
- `smart-router reset --all` removes installed commands and local state
- `smart-router uninstall` removes installed commands, installed share files, and local config/cache (includes saved key)

---

## 13) Common issues and fixes

### A) `smart-router last: command not found`

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
smart-router last
smart-router logs
```

### G) Claude Code says `smart-router/best` may not exist

This message is often a downstream provider/tool-endpoint failure, not a missing local model name.

Run:

```bash
smart-router last
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
- Retry `smart-router status`

### F) Claude Code still using old settings

- Close Claude Code
- Open a fresh terminal
- Start Claude Code again

---

## 14) Security checklist

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

## 15) Update project later

**Modern way (recommended):**

```bash
smart-router upgrade
```

Or re-run the installer:

```bash
./install.sh
```

**Legacy manual update:**

```bash
cd ~/smart-openrouter-router
git pull
cp smart_router.py legacy/smart_router.py
cp legacy/* ~/  # if you still use legacy workflow
chmod +x ~/smart_router_start.sh ~/test_router.sh
router-restart
```

---

## 16) Uninstall

1. **Modern install:**

```bash
smart-router uninstall
```

Or non-interactive:

```bash
smart-router uninstall --yes
```

This removes:

- installed commands in `~/.local/bin`
- installed share files in `~/.local/share/smart-openrouter-router`
- local config in `~/.config/smart-openrouter-router`
- local cache in `~/.cache/smart-openrouter-router`

2. **Legacy manual setup:**
   - Remove router block from `~/.zshrc`
   - Remove files:

```bash
rm -f ~/smart_router.py ~/smart_router_start.sh ~/test_router.sh
rm -f ~/.smart_router.pid ~/.smart_router.log
```

3. Reload shell:

```bash
source ~/.zshrc
```

---

## 17) Quick success checklist

- `smart-router status` returns JSON
- `bash test_install_flow.sh` shows no failures
- Claude Code works with `claude-free`
- `smart-router last` shows final real model and retry count

If all are true, setup is complete.
