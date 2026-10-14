#!/usr/bin/env bash
# Delete exactly the metrics and alert policies that apply.sh creates.
#
# Usage: PROJECT_ID=my-project ./remove.sh [--dry-run]
set -euo pipefail

dry_run=false
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=true
fi
: "${PROJECT_ID:?Set PROJECT_ID to the Google Cloud project ID}"
here="$(cd "$(dirname "$0")" && pwd)"

run() {
  if "$dry_run"; then
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

for file in "$here"/alerts/*.json; do
  title="$(sed -n 's/^  "displayName": "\(.*\)",$/\1/p' "$file")"
  if "$dry_run"; then
    run gcloud alpha monitoring policies delete "<policy named $title>" --project="$PROJECT_ID" --quiet
    continue
  fi
  while read -r name; do
    if [[ -n "$name" ]]; then
      run gcloud alpha monitoring policies delete "$name" --project="$PROJECT_ID" --quiet
    fi
  done < <(gcloud alpha monitoring policies list --project="$PROJECT_ID" \
    --filter="displayName=\"$title\"" --format="value(name)" | tr -d '\r')
done

for file in "$here"/metrics/*.yaml; do
  run gcloud logging metrics delete "$(basename "$file" .yaml)" --project="$PROJECT_ID" --quiet
done
