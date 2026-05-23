#!/usr/bin/env bash
# Run the Competitive Research Assistant inside an OpenShell sandbox
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/output"

# Prerequisites:
# 1. OpenShell gateway running (brew services start openshell)
# 2. Providers configured:
#    openshell provider create --name anthropic --type anthropic --from-existing
#    openshell provider create --name serper --type generic --credential SERPER_API_KEY

mkdir -p "$OUTPUT_DIR"

cd "$SCRIPT_DIR"

# Run the flow inside a sandbox. --keep keeps it alive so we can download.
openshell sandbox create \
  --name research-assistant \
  --keep \
  --policy research-policy.yaml \
  --provider anthropic \
  --provider serper \
  --upload ".:/sandbox/app" \
  -- /bin/bash /sandbox/app/entrypoint.sh

# Download the CSV from the sandbox
echo ""
echo "=== Downloading results ==="
openshell sandbox download research-assistant /sandbox/app/competitors.csv "$OUTPUT_DIR/competitors.csv" 2>/dev/null \
  && echo "Saved to: $OUTPUT_DIR/competitors.csv" \
  && echo "" \
  && cat "$OUTPUT_DIR/competitors.csv" \
  || echo "No competitors.csv found in sandbox."

# Clean up
openshell sandbox delete research-assistant
