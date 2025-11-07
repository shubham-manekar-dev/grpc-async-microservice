#!/usr/bin/env bash
set -euo pipefail

patterns=(
  '^<<<<<<< '
  '^=======$'
  '^>>>>>>> '
)

# Always exclude this script from the scan so that the literal examples above do not
# trigger false positives on CI environments that fall back to plain `grep`.
excludes=(
  ':(exclude)scripts/check_merge_conflicts.sh'
)

for pattern in "${patterns[@]}"; do
  if git grep -n --color=never "$pattern" -- . "${excludes[@]}" >/dev/null 2>&1; then
    echo "Merge conflict markers detected. Please resolve before committing." >&2
    git grep -n --color=never "$pattern" -- . "${excludes[@]}" >&2
    exit 1
  fi
done

echo "No merge conflict markers detected."
