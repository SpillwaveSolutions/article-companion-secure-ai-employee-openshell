#!/usr/bin/env bash
# Run the Competitive Research Assistant inside an OpenShell sandbox
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Prerequisites:
# 1. OpenShell gateway running (brew services start openshell)
# 2. Providers configured:
#    openshell provider create --name anthropic --type anthropic --from-existing
#    openshell provider create --name serper --type generic --credential SERPER_API_KEY

cd "$SCRIPT_DIR"
openshell sandbox create \
  --name research-assistant \
  --policy research-policy.yaml \
  --provider anthropic \
  --provider serper \
  --upload ".:/sandbox/app" \
  -- /bin/bash /sandbox/app/entrypoint.sh
