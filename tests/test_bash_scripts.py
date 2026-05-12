"""Tests that all bash scripts have valid syntax."""

import subprocess
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
ALL_BASH = sorted(EXAMPLES_DIR.rglob("*.sh"))


@pytest.mark.parametrize("sh_path", ALL_BASH, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_bash_syntax(sh_path):
    """Every bash script must pass syntax check (bash -n)."""
    result = subprocess.run(
        ["bash", "-n", str(sh_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Bash syntax error in {sh_path.name}:\n{result.stderr}"
    )


@pytest.mark.parametrize("sh_path", ALL_BASH, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_bash_has_shebang(sh_path):
    """Every bash script must have a proper shebang line."""
    first_line = sh_path.read_text().split("\n")[0]
    assert first_line.startswith("#!/"), f"{sh_path.name} missing shebang"
    assert "bash" in first_line, f"{sh_path.name} shebang doesn't reference bash"


@pytest.mark.parametrize("sh_path", ALL_BASH, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_bash_uses_strict_mode(sh_path):
    """Bash scripts should use set -euo pipefail for safety."""
    content = sh_path.read_text()
    assert "set -euo pipefail" in content, (
        f"{sh_path.name} should use 'set -euo pipefail' for safety"
    )
