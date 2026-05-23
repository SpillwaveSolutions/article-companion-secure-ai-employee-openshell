#!/bin/bash
# entrypoint.sh -- Install deps and run the research flow inside the sandbox
set -euo pipefail

cd /sandbox/app

# Default target if not set by caller
export TARGET_URL="${TARGET_URL:-spillwave.ai}"

# Install CrewAI with Anthropic support
uv pip install --quiet "crewai[anthropic]>=1.14.4" "crewai-tools>=1.14.4"

# Workaround: CrewAI 1.14.x sends strict:true on Anthropic tool definitions,
# but Claude Sonnet 4 doesn't support strict tools yet. Patch it out.
/sandbox/.venv/bin/python -c "
import crewai.llms.providers.anthropic.completion as m
import pathlib
p = pathlib.Path(m.__file__)
src = p.read_text()
src = src.replace('anthropic_tool[\"strict\"] = True', 'pass  # strict tools disabled for Sonnet 4 compat')
p.write_text(src)
"

# Run the flow
/sandbox/.venv/bin/python flow.py
