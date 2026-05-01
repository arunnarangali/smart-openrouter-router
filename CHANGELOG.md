# Changelog

All notable changes to this project are documented in this file.

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
