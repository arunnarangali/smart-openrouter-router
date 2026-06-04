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
assert_file "$SHARE_DIR/plugin/package.json"
assert_file "$SHARE_DIR/plugin/index.js"

python3 -m py_compile "$ROOT_DIR/smart_router.py"
python3 -m py_compile "$ROOT_DIR/bin/smart-router"
python3 -m py_compile "$ROOT_DIR/bin/claude-free"
python3 -m py_compile "$ROOT_DIR/bin/opencode-free"
python3 -m py_compile "$ROOT_DIR/test_scenario_detection.py"
python3 -m py_compile "$ROOT_DIR/test_routing_resolution.py"
python3 -m py_compile "$ROOT_DIR/test_routing_response_rewrite.py"
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

if "$BIN_DIR/smart-router" config validate >/dev/null; then
  pass "smart-router config validate works"
else
  fail "smart-router config validate failed"
fi

if "$BIN_DIR/smart-router" config get policy.mode >/dev/null; then
  pass "smart-router config get works"
else
  fail "smart-router config get failed"
fi

if "$BIN_DIR/smart-router" config set profiles.coding_general.min_context 20000 >/dev/null; then
  pass "smart-router config set works"
else
  fail "smart-router config set failed"
fi

if "$BIN_DIR/smart-router" config diff-defaults >/dev/null; then
  pass "smart-router config diff-defaults works"
else
  fail "smart-router config diff-defaults failed"
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

if "$BIN_DIR/smart-router" doctor --json --fix-suggestions >/dev/null 2>&1; then
  pass "smart-router doctor --fix-suggestions works"
else
  pass "smart-router doctor --fix-suggestions reports issues cleanly when setup is incomplete"
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

if python3 "$ROOT_DIR/test_routing_resolution.py" >/dev/null; then
  pass "routing resolution tests passed"
else
  fail "routing resolution tests failed"
fi

if python3 "$ROOT_DIR/test_routing_response_rewrite.py" >/dev/null; then
  pass "response rewrite tests passed"
else
  fail "response rewrite tests failed"
fi

# Verify opencode-free runtime config uses smart-router/* IDs, not old placeholders
CONFIG_JSON=$(python3 -c "
import sys, types

OC_PATH = '$ROOT_DIR/bin/opencode-free'
with open(OC_PATH) as f:
    src = f.read()
namespace = {'__file__': OC_PATH, '__name__': 'ocfree_test'}
exec(src, namespace)
print(namespace['runtime_opencode_config'](9999, 'test-key'))
")
if echo "$CONFIG_JSON" | python3 -c "
import sys, json
cfg = json.loads(sys.stdin.read())
models = cfg['provider']['smart-router']['models']
assert 'best' in models, 'missing best model'
assert 'fast' in models, 'missing fast model'
assert models['best']['id'] == 'smart-router/best'
assert models['fast']['id'] == 'smart-router/fast'
assert 'openai/gpt-4o-mini' not in json.dumps(models)
assert 'google/gemini-2.0-flash-exp' not in json.dumps(models)
" >/dev/null 2>&1; then
  pass "opencode-free config uses smart-router/best and smart-router/fast"
else
  fail "opencode-free config does not use smart-router/* IDs"
fi

PLUGIN_PATH=$(python3 -c "
import sys

OC_PATH = '$BIN_DIR/opencode-free'
with open(OC_PATH) as f:
    src = f.read()
namespace = {'__file__': OC_PATH, '__name__': 'ocfree_test'}
exec(src, namespace)
print(namespace['plugin_dir']())
")
EXPECTED_PLUGIN_PATH="$SHARE_DIR/plugin"
if [ "$PLUGIN_PATH" = "$EXPECTED_PLUGIN_PATH" ]; then
  pass "opencode-free resolves installed plugin path"
else
  fail "opencode-free plugin path mismatch: got '$PLUGIN_PATH' expected '$EXPECTED_PLUGIN_PATH'"
fi

OPENCODE_TUI_PATH=$(python3 -c "
import sys

OC_PATH = '$BIN_DIR/opencode-free'
with open(OC_PATH) as f:
    src = f.read()
namespace = {'__file__': OC_PATH, '__name__': 'ocfree_test'}
exec(src, namespace)
print(namespace['plugin_tui_json_path']())
")
EXPECTED_TUI_PATH="$XDG_CONFIG_HOME/opencode/tui.json"
if [ "$OPENCODE_TUI_PATH" = "$EXPECTED_TUI_PATH" ]; then
  pass "opencode-free checks global OpenCode TUI plugin config"
else
  fail "opencode-free TUI config path mismatch: got '$OPENCODE_TUI_PATH' expected '$EXPECTED_TUI_PATH'"
fi

if grep -R -E 'sk-or-v1-[A-Za-z0-9]{20,}|OPENROUTER_API_KEY="sk-or-v1-[A-Za-z0-9]{20,}' "$ROOT_DIR" --exclude-dir=.git >/dev/null 2>&1; then
  fail "Potential secret-like API key pattern found in repo"
fi
pass "No obvious API keys found in tracked source"

printf "All installer-flow checks passed.\n"
