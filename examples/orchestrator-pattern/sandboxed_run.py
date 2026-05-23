# sandboxed_run.py -- Helper to spawn sub-agents in their own OpenShell sandboxes
#
# CrewAI has no native OpenShell integration. OpenShell sandboxes at the
# process level: `openshell sandbox create` wraps the entire process in
# Landlock + seccomp + network policy before the first instruction executes.
#
# For multi-agent setups, the orchestrator runs unsandboxed and spawns each
# sub-agent as a separate sandboxed process using this helper.
#
# Key lessons from running the research-assistant example:
# - Use --upload ".:/sandbox/app" to upload code into the sandbox
# - Use --provider to inject credentials (resolved at runtime)
# - Binary paths in policies need globs (/sandbox/.uv/python/**/python3*)
#   because uv's Python path includes the patch version
# - LLM calls should go through https://inference.local (privacy router)
# - The sandbox image has uv and Python pre-installed at /sandbox/.venv

import json
import subprocess


def sandboxed_run(
    policy: str,
    providers: list[str],
    upload_dir: str,
    entrypoint: str,
    task_input: dict | None = None,
) -> dict:
    """Run a sub-agent inside its own OpenShell sandbox.

    Args:
        policy: Path to the OpenShell policy YAML for this sub-agent.
        providers: List of provider names to attach (created via
                   `openshell provider create`).
        upload_dir: Local directory to upload into /sandbox/app.
        entrypoint: Command to run inside the sandbox
                    (e.g. "/bin/bash /sandbox/app/entrypoint.sh").
        task_input: Optional JSON-serializable dict. If provided, written
                    to /sandbox/app/task_input.json before the entrypoint runs.

    Returns:
        The agent's JSON output parsed into a dict.

    Raises:
        subprocess.CalledProcessError: If the sandboxed process exits non-zero.
        json.JSONDecodeError: If the agent's stdout is not valid JSON.
    """
    if task_input is not None:
        input_file = f"{upload_dir}/task_input.json"
        with open(input_file, "w") as f:
            json.dump(task_input, f)

    cmd = [
        "openshell", "sandbox", "create",
        "--policy", policy,
        "--upload", f"{upload_dir}:/sandbox/app",
    ]
    for p in providers:
        cmd.extend(["--provider", p])
    cmd.extend(["--", *entrypoint.split()])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)
