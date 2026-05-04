# Changelog

All notable changes to this project are documented in this file.

## v0.6.0

### Added

- Added Python SDK package `smart_openrouter_router` with:
  - `SmartRouter` lifecycle API (`start`, `stop`, `status`, `last`)
  - `route_chat(messages, ...)`
  - `get_best_model(prompt, scenario=...)`
  - convenience exports: `start_router`, `route_chat`, `get_best_model`
- Added Node backend SDK wrapper in `index.js` with:
  - `createSmartRouter({ apiKey, port, autoStart })`
  - `start`, `stop`, `status`, `last`, `routeChat`, `getBestModel`
- Added packaging metadata updates for SDK export paths.

### Changed

- Kept existing `claude-free` and `opencode-free` runtime behavior unchanged while adding SDK integrations as additive APIs.

### Documentation

- Added SDK integration guidance for Python and Node backends.
- Added React safety guidance (use backend proxy; never expose API key in browser code).

## v0.5.0

### Added

- Added Python packaging metadata via `pyproject.toml` for wheel/sdist builds.
- Added npm packaging metadata via `package.json` with CLI bin mappings.
- Extended release workflow to build and attach:
  - source archive (`smart-openrouter-router-<tag>.tar.gz`)
  - Python wheel + sdist
  - npm tarball (`smart-openrouter-router-*.tgz`)
- Extended release checksums to include all attached package artifacts.

### Documentation

- Documented package/release artifact expectations for pip/npm users.

### Validation

- Python compile checks passed.
- `python3 test_scenario_detection.py` passed.
- `bash test_install_flow.sh` passed.

## v0.4.17

### Added

- Added provider-level runtime stats tracking under `stats.providers` (success/failure counts, avg latency, last status, last update).
- Added stats filters for focused inspection:
  - `smart-router stats --scenario <name>`
  - `smart-router stats --model <id>`
  - `smart-router stats --provider <name>`

### Changed

- Enhanced runtime ranking to factor in provider-level reliability and latency signals from historical stats.
- Extended human stats summary to include tracked provider count.

### Validation

- Python compile checks passed.

## v0.4.16

### Added

- Added config UX commands:
  - `smart-router config get <dotted.key>`
  - `smart-router config set <dotted.key> <value>`
  - `smart-router config validate`
  - `smart-router config diff-defaults`
- Enhanced `smart-router doctor` with:
  - installed file checks under prefix
  - installed-vs-latest version drift check
  - config/stats/cooldowns JSON validity checks
  - log-directory writeability check
  - active PID `/status` reachability check
  - `--fix-suggestions` output mode

### Validation

- Python compile checks passed.
- `python3 test_scenario_detection.py` passed.
- `bash test_install_flow.sh` passed.

## v0.4.15

### Added

- Added `smart-router scenario --explain` to include matched keywords and weights.
- Added `smart-router scenario --compare <file>` to analyze one prompt per line.
- Added grouped human output for `smart-router models --human`.
- Added grouped status field in router `/status` output:
  - `top_per_scenario_grouped`

### Changed

- Extended `smart-router scenario` to support prompt-file batch analysis.
- Improved human-readability workflow while keeping JSON defaults unchanged.

### Validation

- Python compile checks passed.
- `python3 test_scenario_detection.py` passed.
- `bash test_install_flow.sh` passed.

## v0.4.14

### Changed

- Refactored shared scenario/config/filter logic into `smart_router_common.py` to keep runtime router and CLI behavior aligned.
- Updated `smart_router.py` and `bin/smart-router` to use shared analyzer/profile/filter/atomic-write helpers.
- Updated installer to include `smart_router_common.py` in the installed share directory.

### Validation

- Python compile checks passed.
- `bash test_install_flow.sh` passed.

## v0.4.13

### Added

- Added `smart-router doctor` health check command with optional JSON output (`--json`).
- Added compact human-readable output mode (`--human`) for:
  - `smart-router status`
  - `smart-router last`
  - `smart-router cooldowns`
  - `smart-router stats`

### Fixed

- Isolated installer-flow tests with temp `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` to avoid touching real user config/cache.
- Standardized API key precedence in `claude-free` to match `opencode-free`:
  - saved key first
  - env key only when saved key is missing
  - warning when both differ
- Prevented concurrent launcher active-state clobbering by deleting `active.json` only when owned by current launcher PID.
- Added request validation for malformed local requests:
  - invalid `Content-Length` -> `400`
  - invalid/non-object JSON body -> `400`
  - non-list `messages` -> `400`
- Switched config/cache/state JSON writes to atomic temp-file replace pattern.

### Documentation

- Updated command references to modern CLI usage (`smart-router ...`) and added doctor/logs/human output notes.

### Validation

- Python compile checks passed.
- Shell syntax checks passed.
- `python3 test_scenario_detection.py` passed.
- `bash test_install_flow.sh` passed.

## v0.4.12

### Added

- Added Phase 2 scenario visibility in router `/last` output:
  - `detected_scenario`
  - `scenario_scores`
  - `top_scenarios`
  - `scenario_confidence`
- Added `smart-router scenario "prompt text"` command to manually inspect scenario detection.
- Added per-scenario runtime stats under `stats.scenarios` (requests, successes/failures, latency, last model/status).
- Added `test_scenario_detection.py` for common prompt-to-scenario checks.

### Changed

- Extended CLI scenario/config model loops to full scenario set.
- Kept free-only enforcement while respecting client-sent model IDs only when they are exact live free-model matches.

### Validation

- Python compile checks passed.
- `bash test_install_flow.sh` passed.

## v0.4.11

### Added

- Created pip package: `~/smart-router-packages/pip/`
- Created npm package: `~/smart-router-packages/npm/`
- Python pip package wraps existing smart_router.py, includes cli, scripts
- npm package is a thin SDK/client that connects to local Python router

## v0.4.10

### Fixed

- Added Smart Router Build/Plan to OpenCode dropdown with valid IDs.
- Router detects smart-router/* as UI placeholders and ignores them.
- Always uses free model ranking + fallback chain.

## v0.4.9

### Fixed

- Router now ALWAYS uses free model ranking + fallback chain.
- Ignores client-sent model IDs; uses scenario detection from prompt.
- Both opencode-free and claude-free benefit from proper free model selection.

## v0.4.8

### Fixed

- Updated OpenCode launcher config to show 2 models (Build/Plan) with valid IDs.
- Router ignores smart-router UI models and uses scenario detection for all requests.

## v0.4.7

### Fixed

- Added single auto-select model to OpenCode config so models show in dropdown.
- Router still decides which free model to use for each request.

## v0.4.6

### Added

- Added 4 new scenarios: vision, long-context, research, creative
- Router now detects image analysis, document processing, web search, and creative writing
- All new scenarios use free-only model filtering

## v0.4.5

### Fixed

- Removed explicit model IDs from OpenCode launcher config so OpenCode no longer rejects smart-router aliases.
- Router now handles model selection; OpenCode sends requests to the smart-router provider without predefined model mappings.

## v0.4.3

### Fixed

- Added streaming passthrough for OpenAI-compatible requests so OpenCode output appears incrementally when `stream=true`.

## v0.4.4

### Fixed

- Fixed OpenCode launcher model mapping so plan/build resolve to valid `smart-router/*` model IDs.

## v0.4.1

### Added

- Added `smart-router uninstall` for fully removing installed commands and local state with confirmation (supports `--yes`).

### Changed

- `smart-router reset --all` now performs a full uninstall (including `opencode-free` and local config/cache removal).

## v0.4.0

### Added

- Added official `opencode-free` launcher support to the repository and installer so OpenCode can run through the smart router.

### Fixed

- Improved launcher startup reliability by retrying slow router readiness checks instead of crashing on timeout.
- Made router `/status` return quickly without blocking on the initial OpenRouter free-model fetch.

### Documentation

- Updated `README.md`, `FULL_GUIDE.md`, and `CLI_COMMANDS.md` to include OpenCode launcher usage and command references.

### Notes

- This release serves as the first consolidated public release note and highlights capabilities accumulated across previous versions.

## v0.3.9

### Added

- Added tracked `bin/opencode-free` launcher and installer support for running OpenCode through the smart router.

### Changed

- Improved `smart-router setup` UX to clearly show setup context, saved-key state, hidden/visible input mode, and environment-driven setup messaging.
- Refined setup replacement messaging to explicitly state old-key replacement behavior on verify success/failure.
- Added `CLI_COMMANDS.md` with grouped terminal command/help descriptions.

### Fixed

- Fixed launcher startup crashes when router readiness checks hit slow `/status` responses.
- Fixed router `/status` to return quickly without blocking on the initial OpenRouter model fetch.
- Fixed setup key replacement flow in `bin/smart-router` so new keys are verified before write; failed verification no longer overwrites the saved key.
- Fixed setup "current key" display to reflect the saved key state (`~/.config/smart-openrouter-router/api_key`) instead of possibly showing environment-only key context.

## v0.3.3

### Fixed

- Fixed `ANTHROPIC_AUTH_TOKEN` env leak in `bin/claude-free` that could cause "Both token and API key set" Claude Code error.
- Fixed release notes AWK pattern in `.github/workflows/release.yml` to match exact changelog headings (was broken for all versions).
- Added public `cache_age()` method to `ModelCache` class in `smart_router.py` to replace direct private attribute access.
- Removed redundant `cooldowns_active` key from `/status` response in `smart_router.py`.

### Changed

- Moved legacy files (`test_router.sh`, `smart_router_start.sh`, `zshrc_snippet.sh`) to `legacy/` folder.
- Updated `README.md` and `FULL_GUIDE.md` to reflect modern workflow and removed outdated `<system-reminder>` documentation claim.
- Updated version references to `v0.3.3` in install examples.

### Validation

- Python compile checks passed.
- Shell syntax checks passed.
- `bash test_install_flow.sh` passed.

## v0.3.2

### Documentation

- Expanded changelog coverage to include complete release history from `v0.2.0` through `v0.3.1`.
- Added structured per-version summaries for features, fixes, and docs updates.

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

### Fixed

- Restored executable bit for `bin/smart-router` in release artifact.

## v0.2.9

### Fixed

- Fixed installer next-steps messaging after upgrades.
- Installer now suggests `smart-router setup` only when a saved key is missing.

### Documentation

- Updated docs to `v0.2.9` examples and clarified upgrade behavior.

## v0.2.8

### Documentation

- Aligned documentation with `v0.2.7` help output updates.
- Updated version references to `v0.2.8`.

## v0.2.7

### Added

- Added shared help epilog across CLI commands.
- Included setup/upgrade notes in command help output.

## v0.2.6

### Documentation

- Clarified API key persistence during upgrades.
- Clarified when users need to rerun `smart-router setup`.

## v0.2.5

### Added

- Added version and upgrade commands:
  - `smart-router version`
  - `smart-router upgrade`
  - `smart-router upgrade --check`
  - `smart-router upgrade --version <tag>`
- Installer now records installed version metadata.

## v0.2.4

### Added

- Added setup input options:
  - hidden prompt default input
  - `smart-router setup --visible`
  - `smart-router setup --from-env`

### Documentation

- Updated README and guide for new setup input flows.

## v0.2.3

### Fixed

- Fixed checksum lookup handling for curl installer path.
- Improved release notes/install snippets around checksum behavior.

## v0.2.2

### Fixed

- Fixed release archive path/build behavior in GitHub release workflow.

### Documentation

- Updated README and guide version snippets.

## v0.2.1

### Added

- Added curl-based installer (`smart-router-install.sh`).
- Added GitHub Actions release workflow for tagged releases.

### Documentation

- Updated docs for installer-based onboarding.

## v0.2.0

### Added

- Initial smart OpenRouter router toolkit.
- Beginner-friendly `claude-free` launcher workflow.
- Full setup and operations guide.
- Router fallback/visibility improvements and tool-use fallback documentation.
- README quick-start badge and onboarding updates.
