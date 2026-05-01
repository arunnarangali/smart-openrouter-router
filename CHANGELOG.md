# Changelog

All notable changes to this project are documented in this file.

## v0.3.1

### Added

- Added `smart-router models` to show current best live free OpenRouter models by scenario.
- Added `--json` and `--top` options to `smart-router models`.
- Added richer `/last` metadata:
  - `latency_ms`
  - `cooldowns_added`
- Added richer `/status` cooldown visibility:
  - `model_cooldowns_active`
  - `provider_cooldowns_active`

### Changed

- Runtime ranking now applies provider-aware cooldown impact using recent provider failure signals.
- Updated docs and guide examples to include the new model inspection workflow.

### Validation

- Python compile checks passed.
- Shell syntax checks passed.
- `bash test_install_flow.sh` passed.

## v0.3.0

### Added

- Added config management commands:
  - `smart-router config path`
  - `smart-router config view`
  - `smart-router config explain`
  - `smart-router config reset`
  - `smart-router config refresh`
- Added cooldown commands:
  - `smart-router cooldowns`
  - `smart-router cooldowns clear`
- Added stats commands:
  - `smart-router stats`
  - `smart-router stats reset`
- Added free-only config refresh from live OpenRouter model data.

### Changed

- Added config/cooldown/stats-aware ranking in router runtime.
- Improved installer-flow tests and docs.
