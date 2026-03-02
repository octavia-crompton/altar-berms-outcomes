#!/usr/bin/env zsh
# watch_latex.sh
# Auto-recompile any .tex file in this directory when it changes.
# Usage: ./latex/watch_latex.sh          (from project root)
#        ./watch_latex.sh                (from latex/ directory)
#
# Requires: fswatch  (brew install fswatch)

set -e

SCRIPT_DIR="${0:A:h}"          # absolute path of the directory containing this script
cd "$SCRIPT_DIR"

if ! command -v fswatch &>/dev/null; then
    echo "Error: fswatch not found. Install with: brew install fswatch"
    exit 1
fi

if ! command -v pdflatex &>/dev/null; then
    echo "Error: pdflatex not found. Install TeX Live or MacTeX."
    exit 1
fi

compile() {
    local tex="$1"
    local base="${tex:r}"   # strip .tex extension
    echo ""
    echo "[$(date '+%H:%M:%S')] Change detected in ${tex:t} — compiling..."
    if pdflatex -interaction=nonstopmode -halt-on-error "$tex" > "${base}.compile.log" 2>&1; then
        echo "  ✓  ${base:t}.pdf  ($(wc -l < "${base}.compile.log" | tr -d ' ') log lines)"
    else
        echo "  ✗  Compile FAILED — last 10 lines of log:"
        tail -10 "${base}.compile.log" | sed 's/^/      /'
    fi
}

# Initial compile of all .tex files on startup
echo "=== watch_latex.sh starting ==="
echo "Watching: $SCRIPT_DIR/*.tex"
echo "Press Ctrl-C to stop."
echo ""

for tex in "$SCRIPT_DIR"/*.tex; do
    compile "$tex"
done

# Watch for changes and recompile only the affected file
fswatch -0 --event Updated --event Created --include '\.tex$' --exclude '.*' "$SCRIPT_DIR" \
| while IFS= read -r -d '' changed; do
    # fswatch may report the directory itself; filter to .tex files only
    if [[ "$changed" == *.tex ]]; then
        compile "$changed"
    fi
done
