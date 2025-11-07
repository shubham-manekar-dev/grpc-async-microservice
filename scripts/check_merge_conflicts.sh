#!/usr/bin/env bash
set -euo pipefail

pattern_start='^<<<<<<< '
pattern_end='^>>>>>>> '

if git grep -n "$pattern_start" -- . >/dev/null 2>&1; then
  echo "Merge conflict markers detected. Please resolve before committing." >&2
  git grep -n "$pattern_start" -- . >&2
  exit 1
fi

if git grep -n "$pattern_end" -- . >/dev/null 2>&1; then
  echo "Merge conflict markers detected. Please resolve before committing." >&2
  git grep -n "$pattern_end" -- . >&2
  exit 1
fi

if git grep -n '^=======$' -- . >/dev/null 2>&1; then
  echo "Merge conflict markers detected. Please resolve before committing." >&2
  git grep -n '^=======$' -- . >&2
  exit 1
fi

echo "No merge conflict markers detected."
