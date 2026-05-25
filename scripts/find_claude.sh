#!/bin/bash
echo "=== ENV ==="
echo "HOME=$HOME"
echo "SHELL=$SHELL"
echo "PWD=$PWD"
echo "OSTYPE=$OSTYPE"
echo "MSYSTEM=$MSYSTEM"
echo "==="

echo "=== FIND =="
for f in \
    "$HOME/.local/bin/claude" \
    "$HOME/.local/bin/claude.exe" \
    "$HOME/bin/claude" \
    "/c/Users/Administrator/.local/bin/claude" \
    "/c/Users/Administrator/.local/bin/claude.exe" \
    "/mnt/c/Users/Administrator/.local/bin/claude" \
    "/usr/local/bin/claude" \
    "/usr/bin/claude"; do
    if [ -f "$f" ]; then echo "EXISTS: $f"; fi
done
echo "==="

echo "=== PATH ==="
echo "$PATH" | tr ':' '\n'
echo "==="

echo "=== which ==="
which claude 2>&1 || echo "not found"
which claude.exe 2>&1 || echo "not found"
echo "==="

echo "=== ls .local ==="
ls -la "$HOME/.local/bin/" 2>/dev/null || echo "$HOME/.local/bin/ not accessible"
ls -la "/c/Users/Administrator/.local/bin/" 2>/dev/null || echo "/c/Users/Administrator/.local/bin/ not accessible"
echo "==="
