"""Tests that all YAML config files parse correctly and contain expected structure."""

from pathlib import Path

import pytest
import yaml

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


# --------------------------------------------------------------------------- #
# Parametrize over every YAML file in the repo
# --------------------------------------------------------------------------- #

ALL_YAML = sorted(EXAMPLES_DIR.rglob("*.yaml"))


@pytest.mark.parametrize("yaml_path", ALL_YAML, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_yaml_parses(yaml_path):
    """Every YAML file must parse without errors."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    assert data is not None, f"{yaml_path.name} parsed to None"


# --------------------------------------------------------------------------- #
# OpenShell manifest schema: expected top-level keys
# --------------------------------------------------------------------------- #

MANIFEST_FILES = {
    "minimal-sandbox/sandbox.yaml": {"sandbox", "filesystem"},
    "onboarding-executor/manifest.yaml": {
        "sandbox",
        "filesystem",
        "network",
        "process",
        "inference",
        "credentials",
        "audit",
        "approval_gates",
    },
    "research-assistant/sandbox.yaml": {
        "sandbox",
        "filesystem",
        "network",
        "inference",
        "audit",
        "approval_gates",
    },
}


@pytest.mark.parametrize(
    "rel_path,expected_keys",
    MANIFEST_FILES.items(),
    ids=MANIFEST_FILES.keys(),
)
def test_manifest_has_expected_keys(rel_path, expected_keys):
    """OpenShell manifests must contain the expected top-level blocks."""
    path = EXAMPLES_DIR / rel_path
    with open(path) as f:
        data = yaml.safe_load(f)
    actual_keys = set(data.keys())
    missing = expected_keys - actual_keys
    assert not missing, f"Missing keys in {rel_path}: {missing}"


# --------------------------------------------------------------------------- #
# Sandbox identity must be unprivileged
# --------------------------------------------------------------------------- #

SANDBOX_MANIFESTS = [
    EXAMPLES_DIR / "minimal-sandbox/sandbox.yaml",
    EXAMPLES_DIR / "onboarding-executor/manifest.yaml",
    EXAMPLES_DIR / "research-assistant/sandbox.yaml",
]


@pytest.mark.parametrize(
    "manifest", SANDBOX_MANIFESTS, ids=lambda p: p.parent.name
)
def test_sandbox_identity_unprivileged(manifest):
    """All sandbox manifests must use unprivileged identity."""
    with open(manifest) as f:
        data = yaml.safe_load(f)
    identity = data["sandbox"]["identity"]
    assert identity["type"] == "unprivileged", (
        f"{manifest.name}: identity.type must be 'unprivileged', got '{identity['type']}'"
    )


# --------------------------------------------------------------------------- #
# Filesystem: deny_default must be true
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "manifest", SANDBOX_MANIFESTS, ids=lambda p: p.parent.name
)
def test_filesystem_deny_default(manifest):
    """All sandbox manifests must have filesystem.landlock.deny_default: true."""
    with open(manifest) as f:
        data = yaml.safe_load(f)
    landlock = data["filesystem"]["landlock"]
    assert landlock.get("deny_default") is True, (
        f"{manifest.name}: filesystem.landlock.deny_default must be true"
    )


# --------------------------------------------------------------------------- #
# Network: deny_default must be true where present
# --------------------------------------------------------------------------- #


def test_onboarding_network_deny_default():
    """Onboarding manifest must have network.egress.deny_default: true."""
    path = EXAMPLES_DIR / "onboarding-executor/manifest.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data["network"]["egress"]["deny_default"] is True


def test_research_network_deny_default():
    """Research assistant manifest must have network.egress.deny_default: true."""
    path = EXAMPLES_DIR / "research-assistant/sandbox.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data["network"]["egress"]["deny_default"] is True


# --------------------------------------------------------------------------- #
# Inference: deny_default must be true
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "manifest",
    [
        EXAMPLES_DIR / "onboarding-executor/manifest.yaml",
        EXAMPLES_DIR / "research-assistant/sandbox.yaml",
    ],
    ids=["onboarding", "research"],
)
def test_inference_deny_default(manifest):
    """Inference router must be deny-by-default."""
    with open(manifest) as f:
        data = yaml.safe_load(f)
    router = data["inference"]["router"]
    assert router.get("deny_default") is True


# --------------------------------------------------------------------------- #
# Audit: immutable must be true
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "manifest",
    [
        EXAMPLES_DIR / "onboarding-executor/manifest.yaml",
        EXAMPLES_DIR / "research-assistant/sandbox.yaml",
    ],
    ids=["onboarding", "research"],
)
def test_audit_immutable(manifest):
    """Audit logs must be immutable."""
    with open(manifest) as f:
        data = yaml.safe_load(f)
    assert data["audit"].get("immutable") is True


# --------------------------------------------------------------------------- #
# Credential TTLs should not exceed 24h
# --------------------------------------------------------------------------- #


def test_credential_ttl_reasonable():
    """Credential TTLs must not exceed 24h (article gotcha #3)."""
    path = EXAMPLES_DIR / "onboarding-executor/manifest.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    for provider in data["credentials"]["providers"]:
        ttl = provider["ttl"]
        # Parse simple hour format like "4h"
        assert ttl.endswith("h"), f"Expected TTL in hours, got {ttl}"
        hours = int(ttl.rstrip("h"))
        assert hours <= 24, f"TTL {ttl} exceeds 24h"
        # Article recommends matching sandbox lifetime; 4h is reasonable for JIT
        assert hours <= 8, f"TTL {ttl} seems too long for a JIT sandbox"


# --------------------------------------------------------------------------- #
# Seccomp: must forbid ptrace
# --------------------------------------------------------------------------- #


def test_seccomp_forbids_ptrace():
    """Seccomp profile must forbid ptrace."""
    path = EXAMPLES_DIR / "onboarding-executor/manifest.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert "ptrace" in data["process"]["forbid"]


# --------------------------------------------------------------------------- #
# NemoClaw additions: expected keys
# --------------------------------------------------------------------------- #


def test_nemoclaw_additions_structure():
    """NemoClaw additions YAML must have the four differentiating blocks."""
    path = EXAMPLES_DIR / "nemoclaw-diff/nemoclaw-additions.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    expected = {"tools", "credentials", "audit", "policy"}
    actual = set(data.keys())
    assert expected == actual, f"Expected {expected}, got {actual}"


def test_nemoclaw_fail_closed():
    """NemoClaw must default to deny on ambiguity."""
    path = EXAMPLES_DIR / "nemoclaw-diff/nemoclaw-additions.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data["policy"]["on_ambiguity"] == "deny"


def test_nemoclaw_strict_enforcement():
    """NemoClaw must enforce strict tool declaration."""
    path = EXAMPLES_DIR / "nemoclaw-diff/nemoclaw-additions.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data["tools"]["enforce"] == "strict"


# --------------------------------------------------------------------------- #
# Privacy router: must have deny rule for unclassified
# --------------------------------------------------------------------------- #


def test_privacy_router_fail_closed():
    """Privacy router must deny unclassified prompts."""
    path = EXAMPLES_DIR / "enforcement-layers/privacy-router.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    rules = data["inference"]["router"]["rules"]
    # Last rule should be the catch-all deny
    last_rule = rules[-1]
    assert last_rule["match"]["classification"] == "*"
    assert last_rule["action"] == "deny"


# --------------------------------------------------------------------------- #
# Deceptive Landlock: bad example has broad path, good has scoped
# --------------------------------------------------------------------------- #


def test_deceptive_landlock_examples():
    """Gotcha example must show both bad (broad) and good (scoped) paths."""
    path = EXAMPLES_DIR / "gotchas/deceptive-landlock.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    bad_paths = data["filesystem_bad"]["landlock"]["write"]
    good_paths = data["filesystem_good"]["landlock"]["write"]
    # Bad: overly broad /var/log/**
    assert any("/var/log/**" in p for p in bad_paths)
    # Good: scoped to task directory
    assert any("${task_id}" in p for p in good_paths)
