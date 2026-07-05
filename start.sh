#!/bin/bash
# ResearchAgent 一键启动脚本
# Usage: bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Backend ──
echo "=== Starting Backend (port 8000) ==="
cd "$SCRIPT_DIR/backend"
if [ ! -f .env ]; then
    echo "ERROR: backend/.env not found. Copy .env.example and set your API key."
    exit 1
fi
python run.py &
BACKEND_PID=$!

# ── Frontend ──
echo "=== Starting Frontend (port 3000) ==="
cd "$SCRIPT_DIR/frontend"
if [ ! -d node_modules ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
npx next dev -H 0.0.0.0 -p 3000 &
FRONTEND_PID=$!

echo ""
echo "=============================================="
echo "  ResearchAgent is starting..."
echo "  Open: http://$(hostname -I | awk '{print $1}'):3000"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop both services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
