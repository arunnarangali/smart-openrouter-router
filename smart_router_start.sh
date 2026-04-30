#!/usr/bin/env bash
# Auto-starts the Smart OpenRouter Proxy if it is not already running.

PROXY_PORT=8080
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTER_SCRIPT="$SCRIPT_DIR/smart_router.py"
PID_FILE="$HOME/.smart_router.pid"
LOG_FILE="$HOME/.smart_router.log"

port_in_use() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -i ":$PROXY_PORT" -sTCP:LISTEN -t >/dev/null 2>&1
        return $?
    fi

    if command -v ss >/dev/null 2>&1; then
        ss -ltn "sport = :$PROXY_PORT" | grep -q ":$PROXY_PORT"
        return $?
    fi

    return 1
}

start_router() {
    if [ ! -f "$ROUTER_SCRIPT" ]; then
        echo "Smart Router script not found: $ROUTER_SCRIPT"
        return 1
    fi

    echo "Starting Smart Router on port $PROXY_PORT..."
    nohup python3 "$ROUTER_SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 0.8

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Smart Router started (PID $(cat "$PID_FILE"))"
        echo "Logs: $LOG_FILE"
        echo "Status: curl http://127.0.0.1:$PROXY_PORT/status"
    else
        echo "Smart Router failed to start. Check $LOG_FILE"
        return 1
    fi
}

if port_in_use; then
    exit 0
fi

if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE")"
    if kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0
    fi
    rm -f "$PID_FILE"
fi

start_router
