#!/usr/bin/env bash
# Hot-reload: add a domain to a running sandbox's network policy
set -euo pipefail

SANDBOX_NAME="${1:?Usage: hot-reload.sh SANDBOX_NAME}"

# Add a new endpoint to the running sandbox
openshell policy update "$SANDBOX_NAME" \
  --add-endpoint api.newvendor.example.com:443:rest \
  --add-allow api.newvendor.example.com:443:GET:/v1/** \
  --wait

# Verify the update took effect
openshell policy get "$SANDBOX_NAME"
