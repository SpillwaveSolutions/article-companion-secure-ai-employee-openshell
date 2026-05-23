"""Tests that all YAML config files parse correctly and match the real OpenShell schema."""

from pathlib import Path

import pytest
import yaml

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

ALL_YAML = sorted(EXAMPLES_DIR.rglob("*.yaml"))


# --------------------------------------------------------------------------- #
# Basic: every YAML file must parse
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("yaml_path", ALL_YAML, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_yaml_parses(yaml_path):
    """Every YAML file must parse without errors."""
    with open(yaml_path) as f:
        # Should not raise; comment-only files parse to None which is fine
        yaml.safe_load(f)


# --------------------------------------------------------------------------- #
# OpenShell policy schema: version 1 with expected top-level keys
# --------------------------------------------------------------------------- #

POLICY_FILES = {
    "minimal-sandbox/policy.yaml": {
        "version", "filesystem_policy", "landlock", "process", "network_policies",
    },
    "onboarding-executor/onboarding-policy.yaml": {
        "version", "filesystem_policy", "landlock", "process", "network_policies",
    },
    "research-assistant/research-policy.yaml": {
        "version", "filesystem_policy", "landlock", "process", "network_policies",
    },
}


@pytest.mark.parametrize(
    "rel_path,expected_keys",
    POLICY_FILES.items(),
    ids=POLICY_FILES.keys(),
)
def test_policy_has_expected_keys(rel_path, expected_keys):
    """OpenShell policies must contain the expected top-level blocks."""
    path = EXAMPLES_DIR / rel_path
    with open(path) as f:
        data = yaml.safe_load(f)
    actual_keys = set(data.keys())
    missing = expected_keys - actual_keys
    assert not missing, f"Missing keys in {rel_path}: {missing}"


@pytest.mark.parametrize(
    "rel_path",
    POLICY_FILES.keys(),
)
def test_policy_version_is_1(rel_path):
    """All policies must be version 1."""
    path = EXAMPLES_DIR / rel_path
    with open(path) as f:
        data = yaml.safe_load(f)
    assert data["version"] == 1


# --------------------------------------------------------------------------- #
# Process: must run as non-root user
# --------------------------------------------------------------------------- #

POLICY_PATHS = [EXAMPLES_DIR / p for p in POLICY_FILES]


@pytest.mark.parametrize("policy", POLICY_PATHS, ids=lambda p: p.parent.name)
def test_process_not_root(policy):
    """All policies must run as a non-root user."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    proc = data["process"]
    assert proc["run_as_user"] != "root", f"{policy.name}: must not run as root"
    assert proc["run_as_group"] != "root", f"{policy.name}: must not run as root group"


# --------------------------------------------------------------------------- #
# Filesystem: must have read_only or read_write lists
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("policy", POLICY_PATHS, ids=lambda p: p.parent.name)
def test_filesystem_policy_has_paths(policy):
    """All policies must declare filesystem paths."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    fs = data["filesystem_policy"]
    has_read = "read_only" in fs and len(fs["read_only"]) > 0
    has_write = "read_write" in fs and len(fs["read_write"]) > 0
    assert has_read or has_write, f"{policy.name}: must declare at least one path"


@pytest.mark.parametrize("policy", POLICY_PATHS, ids=lambda p: p.parent.name)
def test_filesystem_paths_are_absolute(policy):
    """All filesystem paths must be absolute."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    fs = data["filesystem_policy"]
    for path_list_key in ("read_only", "read_write"):
        for path in fs.get(path_list_key, []):
            assert path.startswith("/"), (
                f"{policy.name}: path '{path}' in {path_list_key} must be absolute"
            )


# --------------------------------------------------------------------------- #
# Landlock compatibility
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("policy", POLICY_PATHS, ids=lambda p: p.parent.name)
def test_landlock_compatibility(policy):
    """Landlock compatibility must be best_effort or hard_requirement."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    compat = data["landlock"]["compatibility"]
    assert compat in ("best_effort", "hard_requirement"), (
        f"{policy.name}: landlock.compatibility must be best_effort or hard_requirement"
    )


# --------------------------------------------------------------------------- #
# Network policies: endpoints must have required fields
# --------------------------------------------------------------------------- #

POLICIES_WITH_NETWORK = [
    EXAMPLES_DIR / "onboarding-executor/onboarding-policy.yaml",
    EXAMPLES_DIR / "research-assistant/research-policy.yaml",
]


@pytest.mark.parametrize("policy", POLICIES_WITH_NETWORK, ids=lambda p: p.parent.name)
def test_network_endpoints_have_required_fields(policy):
    """Each network endpoint must have host, port, protocol, enforcement."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    for policy_key, policy_val in data["network_policies"].items():
        for endpoint in policy_val.get("endpoints", []):
            for field in ("host", "port", "protocol", "enforcement"):
                assert field in endpoint, (
                    f"{policy.name}: endpoint in '{policy_key}' missing '{field}'"
                )


@pytest.mark.parametrize("policy", POLICIES_WITH_NETWORK, ids=lambda p: p.parent.name)
def test_network_enforcement_is_enforce(policy):
    """All endpoints should use 'enforce' mode (not 'audit')."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    for policy_key, policy_val in data["network_policies"].items():
        for endpoint in policy_val.get("endpoints", []):
            assert endpoint["enforcement"] == "enforce", (
                f"{policy.name}: endpoint in '{policy_key}' should enforce, not audit"
            )


# --------------------------------------------------------------------------- #
# Network policies: every policy must have a binaries list
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("policy", POLICIES_WITH_NETWORK, ids=lambda p: p.parent.name)
def test_network_policies_have_binaries(policy):
    """Each network policy must specify which binaries can use it."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    for policy_key, policy_val in data["network_policies"].items():
        binaries = policy_val.get("binaries", [])
        assert len(binaries) > 0, (
            f"{policy.name}: network policy '{policy_key}' missing 'binaries' list. "
            "Without it, no process can match the policy and connections are denied."
        )


@pytest.mark.parametrize("policy", POLICIES_WITH_NETWORK, ids=lambda p: p.parent.name)
def test_binary_paths_use_globs(policy):
    """Binary paths should use globs to handle uv's versioned Python paths."""
    with open(policy) as f:
        data = yaml.safe_load(f)
    for policy_key, policy_val in data["network_policies"].items():
        binaries = policy_val.get("binaries", [])
        python_bins = [b["path"] for b in binaries if "python" in b.get("path", "")]
        if python_bins:
            has_glob = any("*" in p for p in python_bins)
            assert has_glob, (
                f"{policy.name}: policy '{policy_key}' has Python binaries "
                f"without globs: {python_bins}. uv's Python path includes the "
                "patch version (e.g. cpython-3.13.12) which changes across installs. "
                "Use /sandbox/.uv/python/**/python3* to match any version."
            )


# --------------------------------------------------------------------------- #
# NemoClaw additions
# --------------------------------------------------------------------------- #


def test_nemoclaw_additions_structure():
    """NemoClaw additions YAML must have the differentiating blocks."""
    path = EXAMPLES_DIR / "nemoclaw-diff/nemoclaw-additions.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    expected = {"tools", "audit", "policy"}
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
# Deceptive paths: bad example has broad path, good has scoped
# --------------------------------------------------------------------------- #


def test_deceptive_paths_examples():
    """Gotcha example must show both bad (broad) and good (scoped) paths."""
    path = EXAMPLES_DIR / "gotchas/deceptive-paths.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    bad_paths = data["filesystem_policy_bad"]["read_write"]
    good_paths = data["filesystem_policy_good"]["read_write"]
    assert any("/var/log" == p for p in bad_paths), "Bad example should have broad /var/log"
    assert any("onboarding" in p for p in good_paths), "Good example should scope to service"
