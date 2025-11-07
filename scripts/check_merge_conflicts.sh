#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository. Skipping merge conflict scan."
  exit 0
fi

patterns=(
  '^<<<<<<< '
  '^=======$'
  '^>>>>>>> '
)

tracked_files=()
while IFS= read -r -d '' file; do
  tracked_files+=("$file")
done < <(git ls-files -z)

untracked_files=()
while IFS= read -r -d '' file; do
  untracked_files+=("$file")
done < <(git ls-files -o --exclude-standard -z)

all_files=("${tracked_files[@]}" "${untracked_files[@]}")

filtered_files=()
for file in "${all_files[@]}"; do
  if [[ "$file" == "scripts/check_merge_conflicts.sh" ]]; then
    continue
  fi
  if [[ -f "$file" ]]; then
    filtered_files+=("$file")
  fi
done

if [[ ${#filtered_files[@]} -eq 0 ]]; then
  echo "No files to scan."
  exit 0
fi

found=0
for pattern in "${patterns[@]}"; do
  matches=$(printf '%s\0' "${filtered_files[@]}" | xargs -0 -r grep -Hn -E "$pattern" || true)
  if [[ -n "$matches" ]]; then
    if [[ $found -eq 0 ]]; then
      echo "Merge conflict markers detected. Please resolve before committing." >&2
    fi
    found=1
    echo "$matches" >&2
  fi
done

if [[ $found -eq 1 ]]; then
  exit 1
fi

echo "No merge conflict markers detected."
