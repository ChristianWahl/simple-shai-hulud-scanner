#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="${1:-.}"
SCANNER="scanner.py"
LOGFILE="scan-results.log"

RED="\033[0;31m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
NC="\033[0m"

echo "Recursive Repository Scan"
echo "Root directory: $ROOT_DIR"
echo "Scanner script: $SCANNER"
echo "Log file: $LOGFILE"
echo "-----------------------------------------------------"
echo "" > "$LOGFILE"

find "$ROOT_DIR" -type d -name ".git" | while read gitdir; do
    repo="$(dirname "$gitdir")"
    echo -e "${BLUE}Scanning repository:${NC} $repo"

    lockfile=""
    if [ -f "$repo/package-lock.json" ]; then
        lockfile="$repo/package-lock.json"
    elif [ -f "$repo/yarn.lock" ]; then
        lockfile="$repo/yarn.lock"
    fi

    if [ -z "$lockfile" ]; then
        echo -e "  No lockfile found, skipping."
        echo ""
        continue
    fi

    echo -e "  Using lockfile: $lockfile"

    output=$(python "$SCANNER" "$lockfile" || true)

    if [ -z "$output" ]; then
        echo -e "  ${GREEN}No findings${NC}"
    else
        echo -e "  ${RED}Findings detected${NC}:"
        echo "$output" | sed 's/^/    /'

        {
            echo "=== Repository: $repo ==="
            echo "$output"
            echo ""
        } >> "$LOGFILE"
    fi

    echo ""
done

echo "Scan complete."
echo "Results saved to: $LOGFILE"
