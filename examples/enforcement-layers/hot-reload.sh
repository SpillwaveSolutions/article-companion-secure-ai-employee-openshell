#!/usr/bin/env bash
# Hot-reload: add a domain to the egress allowlist without restarting the sandbox
set -euo pipefail

cat >> /etc/openshell/egress-update.yaml <<'EOF'
network:
  egress:
    add:
      - api.newvendor.example.com
EOF

curl -X POST http://localhost:9200/_openshell/policy/reload \
  --data-binary @/etc/openshell/egress-update.yaml

# Verify the reload took effect
openshell policy show --sandbox alex-onboarding-executor --section network.egress
