#!/usr/bin/env bash
# Run the Research Assistant inside an OpenShell sandbox
set -euo pipefail

# Set up inference routing (once per gateway)
# openshell provider create --name anthropic --type anthropic --from-existing
# openshell inference set --provider anthropic --model claude-sonnet-4-20250514

# Create and run the sandboxed agent
openshell sandbox create \
  --name research-assistant \
  --policy research-policy.yaml \
  -- python flow.py

# In another terminal, stream the sandbox logs:
# openshell logs research-assistant --tail
