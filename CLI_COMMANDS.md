# CLI Commands

## Main CLI

- `smart-router` - Smart Router helper CLI
- `claude-free` - Run Claude Code through the router
- `opencode-free` - Run OpenCode through the router

## Setup

- `smart-router setup` - Store and verify OpenRouter API key
- `smart-router setup --from-env` - Read OPENROUTER_API_KEY from env
- `smart-router setup --visible` - Show input while typing

## Runtime Status

- `smart-router status` - Show router status
- `smart-router last` - Show last routed request

## Models

- `smart-router models` - Show current best free models by scenario
- `smart-router models --json` - Output JSON
- `smart-router models --top` - Number of models per scenario

## Version and Upgrade

- `smart-router version` - Show installed version
- `smart-router upgrade` - Upgrade to latest or specific tag
- `smart-router upgrade --check` - Check installed vs latest
- `smart-router upgrade --version` - Install a specific tag (example: v0.3.0)

## Reset

- `smart-router reset` - Reset runtime state
- `smart-router reset --all` - Remove saved key/config and uninstall commands

## Config

- `smart-router config` - Manage router config
- `smart-router config path` - Show config path
- `smart-router config view` - View current config
- `smart-router config explain` - Explain config behavior
- `smart-router config reset` - Reset config to defaults
- `smart-router config refresh` - Refresh best free models in config

## Cooldowns

- `smart-router cooldowns` - Show active cooldowns
- `smart-router cooldowns clear` - Clear all cooldowns

## Stats

- `smart-router stats` - Show model stats
- `smart-router stats reset` - Reset model stats

## Shared Notes

```text
Notes:
  - API key is saved to ~/.config/smart-openrouter-router/api_key
  - Upgrades preserve the saved key; re-run setup only after reset --all, deleting
    ~/.config/smart-openrouter-router/, or if you only use OPENROUTER_API_KEY in
    the current shell/session
  - smart-router upgrade --check exit codes: 0 up-to-date, 2 upgrade available, 1 error
```
