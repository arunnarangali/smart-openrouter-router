#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${SMART_ROUTER_PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
SHARE_DIR="$PREFIX/share/smart-openrouter-router"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/smart-openrouter-router"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/smart-openrouter-router"

mkdir -p "$BIN_DIR" "$SHARE_DIR" "$CONFIG_DIR" "$CACHE_DIR"

cp "$ROOT_DIR/smart_router.py" "$SHARE_DIR/smart_router.py"
cp "$ROOT_DIR/bin/claude-free" "$BIN_DIR/claude-free"
cp "$ROOT_DIR/bin/smart-router" "$BIN_DIR/smart-router"

printf '%s\n' "${SMART_ROUTER_VERSION:-unknown}" > "$SHARE_DIR/VERSION"

chmod +x "$BIN_DIR/claude-free" "$BIN_DIR/smart-router"

echo "Installed: $BIN_DIR/claude-free"
echo "Installed: $BIN_DIR/smart-router"

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
  echo ""
  echo "Add this to your shell profile so commands are found:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
fi

echo ""
echo "Next steps:"
echo "  smart-router setup"
echo "  claude-free"
