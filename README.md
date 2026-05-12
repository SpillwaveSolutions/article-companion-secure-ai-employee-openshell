# Companion Code: Inside Alex's Sandbox

Code samples from **"Inside Alex's Sandbox: An Implementer's Guide to NVIDIA OpenShell + NemoClaw + CrewAI"** by Chris Mathias.

This is the implementer's companion to [Hiring Alex: The Org Chart When Your Newest Employee Is an AI](https://spillwave.com/blog/categories/opinion/2026-04-29-hiring-alex/).

## Structure

```
examples/
  minimal-sandbox/       # Minimal Landlock-pinned sandbox (Section 2)
  enforcement-layers/    # Hot-reload, seccomp, privacy router configs (Section 2)
  nemoclaw-diff/         # What NemoClaw adds to OpenClaw (Section 3)
  onboarding-executor/   # Full manifest + CrewAI Flow (Sections 4-5)
  research-assistant/    # Hello-world digital employee (Section 6)
  gotchas/               # Deceptive Landlock path example (Section 7)
tests/                   # Validation tests for all samples
```

## Prerequisites

- Python 3.11+
- Linux with kernel 5.13+ (for Landlock) or 6.15+ recommended
- [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) installed
- CrewAI 1.14.4+

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests (validates all code samples)
pytest

# Run the hello-world example (requires OpenShell)
cd examples/research-assistant
openshell run --manifest sandbox.yaml --entrypoint "python flow.py"
```

## Running Without OpenShell

The Python code and YAML configs can be validated without OpenShell installed. The test suite checks:

- All YAML files parse correctly and contain expected keys
- All Python files compile and import (with CrewAI installed)
- CrewAI Flow classes have the correct decorator structure
- Bash scripts pass syntax checks
- OpenShell manifests conform to the expected schema

To actually *run* the sandboxed examples, you need OpenShell on a Linux host.

## Related

- [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell)
- [NemoClaw developer blog](https://developer.nvidia.com/blog/build-a-secure-always-on-local-ai-agent-with-nvidia-nemoclaw-and-openclaw/)
- [Penligent security review](https://www.penligent.ai/hackinglabs/nvidia-openclaw-security-what-nemoclaw-changes-and-what-it-still-cannot-fix/)
- [CrewAI documentation](https://docs.crewai.com/)
- [Linux Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html)

## License

Apache 2.0
