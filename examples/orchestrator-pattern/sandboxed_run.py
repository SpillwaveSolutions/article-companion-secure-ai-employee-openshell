# sandboxed_run.py -- Helper to spawn sub-agents in their own OpenShell sandboxes
#
# CrewAI has no native OpenShell integration. OpenShell sandboxes at the
# process level: `openshell run` wraps the entire Python process in a
# Landlock + seccomp + egress policy before the first instruction executes.
#
# For multi-agent setups, the orchestrator runs unsandboxed and spawns each
# sub-agent as a separate sandboxed process using this helper.

import json
import subprocess


def sandboxed_run(manifest: str, task_input: dict) -> dict:
    """Run a sub-agent inside its own OpenShell sandbox.

    Args:
        manifest: Path to the OpenShell manifest YAML for this sub-agent.
        task_input: JSON-serializable dict passed to the agent as input.

    Returns:
        The agent's JSON output parsed into a dict.

    Raises:
        subprocess.CalledProcessError: If the sandboxed process exits non-zero.
        json.JSONDecodeError: If the agent's stdout is not valid JSON.
    """
    result = subprocess.run(
        [
            "openshell",
            "run",
            "--manifest",
            manifest,
            "--entrypoint",
            f"python -m agent --input '{json.dumps(task_input)}'",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)
