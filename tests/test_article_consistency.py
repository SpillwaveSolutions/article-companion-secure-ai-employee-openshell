"""Tests that code samples are consistent with each other.

These tests catch the kind of drift where the YAML config says one thing
and the Python code assumes another.
"""

import importlib.util
import sys
from pathlib import Path

import yaml

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _import_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_research_egress_matches_flow_domains():
    """Research policy egress hosts must match flow.py ALLOWED_DOMAINS."""
    with open(EXAMPLES_DIR / "research-assistant" / "research-policy.yaml") as f:
        policy = yaml.safe_load(f)

    # Extract all endpoint hosts from network_policies
    yaml_hosts = set()
    for policy_val in policy["network_policies"].values():
        for endpoint in policy_val.get("endpoints", []):
            yaml_hosts.add(endpoint["host"])

    mod = _import_module(
        "research_flow_consistency",
        EXAMPLES_DIR / "research-assistant" / "flow.py",
    )
    python_domains = mod.ALLOWED_DOMAINS

    assert yaml_hosts == python_domains, (
        f"Policy endpoint hosts {yaml_hosts} don't match "
        f"Python ALLOWED_DOMAINS {python_domains}"
    )


def test_onboarding_policy_has_four_services():
    """Onboarding policy must have four named network policies."""
    with open(EXAMPLES_DIR / "onboarding-executor" / "onboarding-policy.yaml") as f:
        policy = yaml.safe_load(f)
    policies = policy["network_policies"]
    assert len(policies) == 4, f"Expected 4 network policies, got {len(policies)}"
    expected = {"identity_provider", "microsoft_graph", "calendar", "slack"}
    assert set(policies.keys()) == expected


def test_all_policies_are_version_1():
    """Every OpenShell policy must be version 1."""
    for rel_path in [
        "minimal-sandbox/policy.yaml",
        "onboarding-executor/onboarding-policy.yaml",
        "research-assistant/research-policy.yaml",
    ]:
        path = EXAMPLES_DIR / rel_path
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["version"] == 1, f"{rel_path}: must be version 1"


def test_all_policies_deny_by_default():
    """OpenShell policies deny by default; there's no deny_default key needed.

    This test verifies we're NOT using the old invented deny_default pattern.
    """
    for rel_path in [
        "minimal-sandbox/policy.yaml",
        "onboarding-executor/onboarding-policy.yaml",
        "research-assistant/research-policy.yaml",
    ]:
        path = EXAMPLES_DIR / rel_path
        content = path.read_text()
        assert "deny_default" not in content, (
            f"{rel_path}: should not have deny_default (deny-by-default is inherent)"
        )


def test_no_invented_uri_schemes():
    """No files should use the invented claude-on-prem:// or nemotron-local:// schemes."""
    for path in EXAMPLES_DIR.rglob("*"):
        if path.is_file() and path.suffix in (".yaml", ".py", ".sh"):
            content = path.read_text()
            assert "claude-on-prem://" not in content, (
                f"{path.name}: uses invented claude-on-prem:// URI"
            )
            assert "nemotron-local://" not in content, (
                f"{path.name}: uses invented nemotron-local:// URI"
            )


def test_no_invented_cli_commands():
    """No files should use invented OpenShell CLI commands."""
    invented_commands = [
        "openshell run ",
        "openshell validate ",
        "openshell init ",
        "openshell drain ",
        "openshell policy show ",
    ]
    for path in EXAMPLES_DIR.rglob("*"):
        if path.is_file() and path.suffix in (".yaml", ".py", ".sh"):
            content = path.read_text()
            for cmd in invented_commands:
                assert cmd not in content, (
                    f"{path.name}: uses invented command '{cmd.strip()}'"
                )


def test_seccomp_extension_is_documentation():
    """Seccomp extension file should be documentation, not a runnable config."""
    path = EXAMPLES_DIR / "enforcement-layers" / "seccomp-extension.yaml"
    content = path.read_text()
    # Should be comments only (documentation), since seccomp is automatic
    non_comment_lines = [
        line for line in content.strip().split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    assert len(non_comment_lines) == 0, (
        "seccomp-extension.yaml should be pure documentation (comments only)"
    )


def test_privacy_router_is_documentation():
    """Privacy router file should be documentation, since it's configured via CLI."""
    path = EXAMPLES_DIR / "enforcement-layers" / "privacy-router.yaml"
    content = path.read_text()
    non_comment_lines = [
        line for line in content.strip().split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    assert len(non_comment_lines) == 0, (
        "privacy-router.yaml should be pure documentation (comments only)"
    )
