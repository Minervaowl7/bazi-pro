#!/bin/bash
# Ralph Wiggum Dev Loop — bazi-pro 自治开发循环
# 用法:
#   bash scripts/ralph_dev_loop.sh              # 无限循环
#   bash scripts/ralph_dev_loop.sh --dry-run    # 只打印不执行
#   bash scripts/ralph_dev_loop.sh --max 10     # 最多10轮
#
# 前置条件:
#   1. SSH key 已添加到 GitHub (git remote 用 SSH)
#   2. claude CLI 可用
#   3. PROMPT.md 存在于项目根目录

set -euo pipefail

# Ensure Claude CLI is findable — try multiple known locations
_find_claude() {
    for candidate in \
        "$HOME/.local/bin/claude" \
        "$HOME/.local/bin/claude.exe" \
        "$HOME/bin/claude" \
        "/c/Users/Administrator/.local/bin/claude" \
        "/c/Users/Administrator/.local/bin/claude.exe" \
        "/mnt/c/Users/Administrator/.local/bin/claude" \
        "/mnt/c/Users/Administrator/.local/bin/claude.exe" \
        "/usr/local/bin/claude" \
        "/usr/bin/claude"; do
        if [ -x "$candidate" ]; then
            CLAUDE_BIN="$candidate"
            return 0
        fi
    done
    # Try command -v for both claude and claude.exe
    if found="$(command -v claude 2>/dev/null || command -v claude.exe 2>/dev/null)"; then
        CLAUDE_BIN="$found"
        return 0
    fi
    return 1
}

if ! _find_claude; then
    echo "ERROR: 'claude' CLI not found."
    echo "  Tried: ~/.local/bin/claude[.exe], /mnt/c/Users/Administrator/.local/bin/claude[.exe], /usr/local/bin/claude"
    exit 1
fi
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROMPT_FILE="$PROJECT_DIR/PROMPT.md"
LOG_DIR="$PROJECT_DIR/.ralph_logs"

MAX_ROUNDS=0
DRY_RUN=false
MAX_CONSECUTIVE_FAILURES=3
MAX_TASK_RETRIES=5

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --max) MAX_ROUNDS="$2"; shift ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
    shift
done

if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: PROMPT.md not found at $PROMPT_FILE"
    exit 1
fi

# (claude path already resolved above in _find_claude)

mkdir -p "$LOG_DIR"

round=0
consecutive_failures=0
last_task=""
task_attempts=0

log_file="$LOG_DIR/ralph_$(date +%Y%m%d_%H%M%S).log"
log() {
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$ts] $*" | tee -a "$log_file"
}

count_remaining() {
    grep -c '^\- \[ \]' "$PROMPT_FILE" 2>/dev/null || echo "0"
}

current_task_text() {
    grep '^\- \[ \]' "$PROMPT_FILE" | head -1 2>/dev/null || echo "(no tasks remaining)"
}

cleanup() {
    log ""
    log "=========================================="
    log " Ralph goes home now."
    log "=========================================="
    log "  Rounds: $round"
    log "  Remaining tasks: $(count_remaining)"
    log "  Consecutive failures: $consecutive_failures"
    log "  Log: $log_file"
    log ""
    log "  'My cat's breath smells like cat food!'"
    exit 0
}
trap cleanup SIGINT SIGTERM

commit_and_push() {
    if git diff --quiet && git diff --cached --quiet; then
        log "No changes to commit."
        return 1
    fi

    git add -u
    git add "$PROMPT_FILE" 2>/dev/null || true

    if git diff --cached --quiet; then
        log "Nothing staged."
        return 1
    fi

    local task_line="$(current_task_text)"
    local msg="Auto: $(echo "$task_line" | sed 's/^\- \[ \] //' | head -c 80)"
    git commit -m "$msg" 2>&1 | tail -1

    if git push origin main 2>&1; then
        log "Pushed to GitHub."
        return 0
    else
        log "WARNING: git push failed."
        return 1
    fi
}

run_claude() {
    log ">> Invoking Claude with PROMPT.md ($(wc -c < "$PROMPT_FILE") bytes)..."

    if $DRY_RUN; then
        log "  [DRY RUN] Would run: claude -p \"\$(cat PROMPT.md)\" --dangerously-skip-permissions < /dev/null"
        sleep 2
        return 0
    fi

    local exit_code=0
    cd "$PROJECT_DIR"
    "$CLAUDE_BIN" -p "$(cat "$PROMPT_FILE")" --dangerously-skip-permissions < /dev/null 2>&1 | tee -a "$log_file" || exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log "Claude exited OK."
    else
        log "Claude exited with code $exit_code."
    fi
    return $exit_code
}

# ── Main Loop ──────────────────────────────────

log "=========================================="
log " RALPH WIGGUM DEV LOOP"
log " bazi-pro overnight autonomous mode"
log "=========================================="
log "  Project: $PROJECT_DIR"
log "  Prompt: $PROMPT_FILE"
log "  Dry run: $DRY_RUN"
log "  Max rounds: ${MAX_ROUNDS:-unlimited}"
log "  $(count_remaining) tasks remaining"
log ""

while true; do
    round=$((round + 1))
    remaining=$(count_remaining)

    if [ "$remaining" -eq 0 ]; then
        log "ALL TASKS DONE! Ralph says: I'm a winner!"
        commit_and_push || true
        exit 0
    fi

    current="$(current_task_text)"
    log ""
    log "-- Round $round --"
    log "  Remaining: $remaining tasks"
    log "  Current: $current"

    if [ "$current" = "$last_task" ]; then
        task_attempts=$((task_attempts + 1))
        if [ $task_attempts -ge $MAX_TASK_RETRIES ]; then
            log "MAX RETRIES reached for: $current"
            log "Skipping. Human intervention needed."
            exit 1
        fi
    else
        task_attempts=0
        last_task="$current"
    fi

    if run_claude; then
        consecutive_failures=0
        commit_and_push || log "Commit/push skipped."
    else
        consecutive_failures=$((consecutive_failures + 1))
        log "  FAILURE streak: $consecutive_failures"

        if [ $consecutive_failures -ge $MAX_CONSECUTIVE_FAILURES ]; then
            log ""
            log "=========================================="
            log "  CIRCUIT BREAKER TRIPPED"
            log "  $consecutive_failures consecutive failures"
            log "  Human intervention needed!"
            log "=========================================="
            exit 1
        fi
    fi

    if [ "$MAX_ROUNDS" -gt 0 ] && [ "$round" -ge "$MAX_ROUNDS" ]; then
        log "Reached max rounds ($MAX_ROUNDS)."
        exit 0
    fi

    sleep 5
done
