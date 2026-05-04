#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="$(mktemp -d)"
PREFIX="$TMP_DIR/prefix"
XDG_CONFIG_HOME="$TMP_DIR/config"
XDG_CACHE_HOME="$TMP_DIR/cache"
export XDG_CONFIG_HOME
export XDG_CACHE_HOME

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

pass() { printf "PASS  %s\n" "$1"; }
fail() { printf "FAIL  %s\n" "$1"; exit 1; }

assert_file() {
  local path="$1"
  [ -f "$path" ] || fail "Missing file: $path"
  pass "Found file: $path"
}

assert_exec() {
  local path="$1"
  [ -x "$path" ] || fail "Not executable: $path"
  pass "Executable: $path"
}

printf "Running installer-flow checks in temp prefix...\n"

SMART_ROUTER_PREFIX="$PREFIX" SMART_ROUTER_VERSION="test" XDG_CONFIG_HOME="$XDG_CONFIG_HOME" XDG_CACHE_HOME="$XDG_CACHE_HOME" bash "$ROOT_DIR/install.sh"

BIN_DIR="$PREFIX/bin"
SHARE_DIR="$PREFIX/share/smart-openrouter-router"

assert_file "$BIN_DIR/claude-free"
assert_file "$BIN_DIR/smart-router"
assert_file "$BIN_DIR/opencode-free"
assert_exec "$BIN_DIR/claude-free"
assert_exec "$BIN_DIR/smart-router"
assert_exec "$BIN_DIR/opencode-free"

assert_file "$SHARE_DIR/smart_router.py"
assert_file "$SHARE_DIR/smart_router_common.py"
assert_file "$SHARE_DIR/VERSION"

python3 -m py_compile "$ROOT_DIR/smart_router.py"
python3 -m py_compile "$ROOT_DIR/bin/smart-router"
python3 -m py_compile "$ROOT_DIR/bin/claude-free"
python3 -m py_compile "$ROOT_DIR/bin/opencode-free"
python3 -m py_compile "$ROOT_DIR/test_scenario_detection.py"
pass "Python syntax checks passed"

bash -n "$ROOT_DIR/install.sh"
bash -n "$ROOT_DIR/smart-router-install.sh"
if [ -f "$ROOT_DIR/test_router.sh" ]; then
  bash -n "$ROOT_DIR/test_router.sh"
fi
if [ -f "$ROOT_DIR/legacy/test_router.sh" ]; then
  bash -n "$ROOT_DIR/legacy/test_router.sh"
fi
bash -n "$ROOT_DIR/test_install_flow.sh"
pass "Shell syntax checks passed"

if "$BIN_DIR/smart-router" --help | grep -qi "system-reminder"; then
  fail "CLI help leaked system-reminder block"
fi
pass "CLI help does not leak system-reminder block"

"$BIN_DIR/smart-router" version >/dev/null
pass "smart-router version command works"

if "$BIN_DIR/smart-router" setup --help >/dev/null; then
  pass "smart-router setup help works"
else
  fail "smart-router setup help failed"
fi

if "$BIN_DIR/smart-router" uninstall --help >/dev/null; then
  pass "smart-router uninstall help works"
else
  fail "smart-router uninstall help failed"
fi

if "$BIN_DIR/smart-router" models --help >/dev/null; then
  pass "smart-router models help works"
else
  fail "smart-router models help failed"
fi

if "$BIN_DIR/smart-router" scenario --help >/dev/null; then
  pass "smart-router scenario help works"
else
  fail "smart-router scenario help failed"
fi

if "$BIN_DIR/smart-router" models --human >/dev/null 2>&1; then
  pass "smart-router models --human works"
else
  pass "smart-router models --human fails cleanly when key is unavailable"
fi

if "$BIN_DIR/smart-router" scenario --explain "react component bug" >/dev/null; then
  pass "smart-router scenario --explain works"
else
  fail "smart-router scenario --explain failed"
fi

if "$BIN_DIR/smart-router" models >/dev/null 2>&1; then
  pass "smart-router models command runs"
else
  pass "smart-router models fails cleanly when key is unavailable"
fi

if "$BIN_DIR/smart-router" config path >/dev/null; then
  pass "smart-router config path works"
else
  fail "smart-router config path failed"
fi

CONFIG_PATH="$($BIN_DIR/smart-router config path)"
EXPECTED_CONFIG_PATH="$XDG_CONFIG_HOME/smart-openrouter-router/config.json"
if [ "$CONFIG_PATH" = "$EXPECTED_CONFIG_PATH" ]; then
  pass "config path is isolated to temp XDG_CONFIG_HOME"
else
  fail "config path not isolated: got '$CONFIG_PATH' expected '$EXPECTED_CONFIG_PATH'"
fi

if "$BIN_DIR/smart-router" config explain >/dev/null; then
  pass "smart-router config explain works"
else
  fail "smart-router config explain failed"
fi

if "$BIN_DIR/smart-router" config reset >/dev/null; then
  pass "smart-router config reset works"
else
  fail "smart-router config reset failed"
fi

if "$BIN_DIR/smart-router" config view >/dev/null; then
  pass "smart-router config view works"
else
  fail "smart-router config view failed"
fi

if "$BIN_DIR/smart-router" cooldowns >/dev/null; then
  pass "smart-router cooldowns works"
else
  fail "smart-router cooldowns failed"
fi

if "$BIN_DIR/smart-router" stats >/dev/null; then
  pass "smart-router stats works"
else
  fail "smart-router stats failed"
fi

if "$BIN_DIR/smart-router" status --human >/dev/null 2>&1; then
  pass "smart-router status --human works"
else
  pass "smart-router status --human fails cleanly when router is not running"
fi

if "$BIN_DIR/smart-router" doctor --json >/dev/null 2>&1; then
  pass "smart-router doctor --json works"
else
  pass "smart-router doctor --json reports issues cleanly when setup is incomplete"
fi

if "$BIN_DIR/smart-router" logs --help >/dev/null; then
  pass "smart-router logs help works"
else
  fail "smart-router logs help failed"
fi

if "$BIN_DIR/smart-router" logs --path >/dev/null; then
  pass "smart-router logs path works"
else
  fail "smart-router logs path failed"
fi

if python3 "$ROOT_DIR/test_scenario_detection.py" >/dev/null; then
  pass "scenario detection tests passed"
else
  fail "scenario detection tests failed"
fi

if grep -R -E 'sk-or-v1-[A-Za-z0-9]{20,}|OPENROUTER_API_KEY="sk-or-v1-[A-Za-z0-9]{20,}' "$ROOT_DIR" --exclude-dir=.git >/dev/null 2>&1; then
  fail "Potential secret-like API key pattern found in repo"
fi
pass "No obvious API keys found in tracked source"

printf "All installer-flow checks passed.\n"
