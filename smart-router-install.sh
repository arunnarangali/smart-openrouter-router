#!/usr/bin/env bash
set -euo pipefail

REPO="arunnarangali/smart-openrouter-router"
VERSION="${SMART_ROUTER_VERSION:-latest}"
PREFIX="${SMART_ROUTER_PREFIX:-$HOME/.local}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd curl
need_cmd tar
need_cmd python3

if [ "$VERSION" = "latest" ]; then
  echo "Installing latest release (not pinned)." >&2
  TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | python3 - <<'PY'
import json
import sys

data = json.loads(sys.stdin.read())
print(data.get("tag_name", ""))
PY
  )
  if [ -z "$TAG" ]; then
    echo "Failed to resolve latest release tag." >&2
    exit 1
  fi
else
  TAG="$VERSION"
fi

ARCHIVE="smart-openrouter-router-${TAG}.tar.gz"
BASE_URL="https://github.com/$REPO/releases/download/$TAG"
ARCHIVE_URL="$BASE_URL/$ARCHIVE"
CHECKSUM_URL="$BASE_URL/SHA256SUMS"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

curl -fsSL -o "$TMP_DIR/$ARCHIVE" "$ARCHIVE_URL"
curl -fsSL -o "$TMP_DIR/SHA256SUMS" "$CHECKSUM_URL"

EXPECTED=$(python3 - <<PY
import re
from pathlib import Path

checksum_path = Path("$TMP_DIR") / "SHA256SUMS"
archive = "$ARCHIVE"
expected = ""
for line in checksum_path.read_text(encoding="utf-8").splitlines():
    parts = line.strip().split()
    if len(parts) >= 2:
        name = parts[1].lstrip("*").split("/")[-1]
        if name == archive:
            expected = parts[0]
            break
print(expected)
PY
)

if [ -z "$EXPECTED" ]; then
  echo "Checksum entry not found for $ARCHIVE" >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL=$(sha256sum "$TMP_DIR/$ARCHIVE" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  ACTUAL=$(shasum -a 256 "$TMP_DIR/$ARCHIVE" | awk '{print $1}')
else
  echo "Missing checksum tool (sha256sum or shasum)." >&2
  exit 1
fi

if [ "$EXPECTED" != "$ACTUAL" ]; then
  echo "Checksum verification failed." >&2
  echo "Expected: $EXPECTED" >&2
  echo "Actual:   $ACTUAL" >&2
  exit 1
fi

tar -xzf "$TMP_DIR/$ARCHIVE" -C "$TMP_DIR"
SOURCE_DIR="$TMP_DIR/smart-openrouter-router-$TAG"
if [ ! -d "$SOURCE_DIR" ]; then
  echo "Extracted folder not found: $SOURCE_DIR" >&2
  exit 1
fi

SMART_ROUTER_VERSION="$TAG" SMART_ROUTER_PREFIX="$PREFIX" bash "$SOURCE_DIR/install.sh"

echo ""
echo "Next steps:"
echo "  smart-router setup"
echo "  claude-free"
