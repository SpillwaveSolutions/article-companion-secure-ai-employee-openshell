# sandboxed_run.py -- Helper to spawn sub-agents in their own OpenShell sandboxes
#
# CrewAI has no native OpenShell integration. OpenShell sandboxes at the
# process level: `openshell sandbox create` wraps the entire process in
# Landlock + seccomp + network policy before the first instruction executes.
#
# For multi-agent setups, the orchestrator runs unsandboxed and spawns each
# sub-agent as a separate sandboxed process using this helper.

import json
import subprocess


def sandboxed_run(
    policy: str, providers: list[str], command: str, task_input: dict
) -> dict:
    """Run a sub-agent inside its own OpenShell sandbox.

    Args:
        policy: Path to the OpenShell policy YAML for this sub-agent.
        providers: List of provider names to attach (created via
                   `openshell provider create`).
        command: The entrypoint command to run inside the sandbox.
        task_input: JSON-serializable dict passed as an argument to the command.

    Returns:
        The agent's JSON output parsed into a dict.

    Raises:
        subprocess.CalledProcessError: If the sandboxed process exits non-zero.
        json.JSONDecodeError: If the agent's stdout is not valid JSON.
    """
    cmd = ["openshell", "sandbox", "create", "--policy", policy]
    for p in providers:
        cmd.extend(["--provider", p])
    cmd.extend(["--", command, json.dumps(task_input)])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)
