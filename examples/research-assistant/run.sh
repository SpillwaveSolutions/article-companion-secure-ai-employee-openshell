#!/usr/bin/env bash
# Run the Research Assistant inside an OpenShell sandbox
set -euo pipefail

openshell run --manifest sandbox.yaml --entrypoint "python flow.py"

# In another terminal, watch the audit log fill in real time:
# tail -f /var/log/research/audit.jsonl | jq '.level, .event'
