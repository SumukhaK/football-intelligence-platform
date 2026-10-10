#!/usr/bin/env bash
# Create or update the football-api log-based metrics and alert policies.
#
# Usage: PROJECT_ID=<project id> NOTIFICATION_CHANNEL=<email channel full name> \
#          ./apply.sh [--dry-run]
#
# Metrics are updated in place when they exist. Alert policies are matched by
# display name: an existing one is deleted and created again from its file, so
# running this twice leaves exactly one of each. --dry-run prints the gcloud
# commands without running any.
set -euo pipefail

dry_run=false
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=true
fi
: "${PROJECT_ID:?Set PROJECT_ID to the Google Cloud project ID}"
: "${NOTIFICATION_CHANNEL:?Set NOTIFICATION_CHANNEL to the full name of the email channel}"
here="$(cd "$(dirname "$0")" && pwd)"

run() {
  if "$dry_run"; then
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

metric_exists() {
  ! "$dry_run" && gcloud logging metrics describe "$1" --project="$PROJECT_ID" >/dev/null 2>&1
}

policy_names() {
  "$dry_run" && return 0
  gcloud alpha monitoring policies list --project="$PROJECT_ID" \
    --filter="displayName=\"$1\"" --format="value(name)"
}

display_name() {
  sed -n 's/^  "displayName": "\(.*\)",$/\1/p' "$1"
}

for file in "$here"/metrics/*.yaml; do
  name="$(basename "$file" .yaml)"
  verb=create
  if metric_exists "$name"; then
    verb=update
  fi
  run gcloud logging metrics "$verb" "$name" --config-from-file="$file" --project="$PROJECT_ID"
done

for file in "$here"/alerts/*.json; do
  while read -r old; do
    if [[ -n "$old" ]]; then
      gcloud alpha monitoring policies delete "$old" --project="$PROJECT_ID" --quiet
    fi
  done < <(policy_names "$(display_name "$file")")
  run gcloud alpha monitoring policies create --policy-from-file="$file" \
    --notification-channels="$NOTIFICATION_CHANNEL" --project="$PROJECT_ID"
done
