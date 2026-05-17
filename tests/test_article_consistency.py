"""Tests that code samples are consistent with each other.

These tests catch the kind of drift where the YAML config says one thing
and the Python code assumes another.
"""

from pathlib import Path

import yaml

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_research_egress_matches_flow_domains():
    """Research sandbox.yaml egress allowlist must match flow.py ALLOWED_DOMAINS."""
    # Load YAML allowlist
    with open(EXAMPLES_DIR / "research-assistant" / "sandbox.yaml") as f:
        manifest = yaml.safe_load(f)
    yaml_domains = set(manifest["network"]["egress"]["allow"])

    # Load Python ALLOWED_DOMAINS
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "research_flow",
        EXAMPLES_DIR / "research-assistant" / "flow.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["research_flow"] = mod
    spec.loader.exec_module(mod)
    python_domains = mod.ALLOWED_DOMAINS

    assert yaml_domains == python_domains, (
        f"YAML egress allowlist {yaml_domains} doesn't match "
        f"Python ALLOWED_DOMAINS {python_domains}"
    )


def test_research_inference_backend_matches_flow_llm():
    """Research sandbox.yaml inference backend must match flow.py LLM_BACKEND."""
    with open(EXAMPLES_DIR / "research-assistant" / "sandbox.yaml") as f:
        manifest = yaml.safe_load(f)
    yaml_backends = set(manifest["inference"]["router"]["allow"])

    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "research_flow_2",
        EXAMPLES_DIR / "research-assistant" / "flow.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["research_flow_2"] = mod
    spec.loader.exec_module(mod)
    llm_backend = mod.LLM_BACKEND

    assert llm_backend in yaml_backends, (
        f"LLM_BACKEND '{llm_backend}' not in sandbox inference allowlist {yaml_backends}"
    )


def test_onboarding_sandbox_is_jit():
    """Onboarding executor must use JIT lifetime (article section 4)."""
    with open(EXAMPLES_DIR / "onboarding-executor" / "manifest.yaml") as f:
        manifest = yaml.safe_load(f)
    assert manifest["sandbox"]["lifetime"] == "jit"


def test_research_sandbox_is_jit():
    """Research assistant must use JIT lifetime (hello-world section)."""
    with open(EXAMPLES_DIR / "research-assistant" / "sandbox.yaml") as f:
        manifest = yaml.safe_load(f)
    assert manifest["sandbox"]["lifetime"] == "jit"


def test_onboarding_approval_gate_timeout():
    """Onboarding approval gate timeout must be 30m (matches article)."""
    with open(EXAMPLES_DIR / "onboarding-executor" / "manifest.yaml") as f:
        manifest = yaml.safe_load(f)
    gate = manifest["approval_gates"][0]
    assert gate["timeout"] == "30m"
    assert gate["require"] == "human_approval"


def test_seccomp_extension_preserves_base_forbids():
    """Seccomp extension must still forbid ptrace, exec_setuid, kmod_load."""
    with open(EXAMPLES_DIR / "enforcement-layers" / "seccomp-extension.yaml") as f:
        data = yaml.safe_load(f)
    forbid = data["process"]["forbid"]
    for syscall in ["ptrace", "exec_setuid", "kmod_load"]:
        assert syscall in forbid, f"Seccomp extension must still forbid {syscall}"


def test_privacy_router_has_phi_route():
    """Privacy router must route PHI to a local model (not a public endpoint)."""
    with open(EXAMPLES_DIR / "enforcement-layers" / "privacy-router.yaml") as f:
        data = yaml.safe_load(f)
    rules = data["inference"]["router"]["rules"]
    phi_rule = next(r for r in rules if r["match"]["classification"] == "phi")
    assert "ollama" in phi_rule["backend"], (
        "PHI must route to a local model (ollama), not a public endpoint"
    )


def test_all_manifests_have_deny_default_pattern():
    """Every sandbox manifest must follow the deny-by-default pattern.

    This is the core security posture of the article: every layer that has
    a policy must default to deny.
    """
    manifests = [
        EXAMPLES_DIR / "onboarding-executor" / "manifest.yaml",
        EXAMPLES_DIR / "research-assistant" / "sandbox.yaml",
    ]
    for path in manifests:
        with open(path) as f:
            data = yaml.safe_load(f)
        # Filesystem
        assert data["filesystem"]["landlock"]["deny_default"] is True, (
            f"{path.name}: filesystem must deny by default"
        )
        # Network
        assert data["network"]["egress"]["deny_default"] is True, (
            f"{path.name}: network must deny by default"
        )
        # Inference
        assert data["inference"]["router"]["deny_default"] is True, (
            f"{path.name}: inference must deny by default"
        )
