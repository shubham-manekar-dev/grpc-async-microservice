#!/usr/bin/env bash
set -euo pipefail

if git grep -n "<<<<<<< " -- . >/dev/null 2>&1; then
  echo "Merge conflict markers detected. Please resolve before committing." >&2
  git grep -n "<<<<<<< " -- . >&2
  exit 1
fi

if git grep -n ">>>>>>>" -- . >/dev/null 2>&1; then
  echo "Merge conflict markers detected. Please resolve before committing." >&2
  git grep -n ">>>>>>>" -- . >&2
  exit 1
fi

echo "No merge conflict markers detected."
