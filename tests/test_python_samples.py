"""Tests that all Python code samples compile, import, and have correct structure."""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
ALL_PYTHON = sorted(EXAMPLES_DIR.rglob("*.py"))


# --------------------------------------------------------------------------- #
# Syntax: every Python file must parse
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("py_path", ALL_PYTHON, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_python_syntax(py_path):
    """Every Python file must be valid syntax."""
    source = py_path.read_text()
    ast.parse(source, filename=str(py_path))


# --------------------------------------------------------------------------- #
# Import: every Python file must import without error
# --------------------------------------------------------------------------- #


def _import_module_from_path(path: Path):
    """Import a Python file as a module without running __main__ blocks."""
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("py_path", ALL_PYTHON, ids=lambda p: str(p.relative_to(EXAMPLES_DIR)))
def test_python_imports(py_path):
    """Every Python file must import without errors."""
    _import_module_from_path(py_path)


# --------------------------------------------------------------------------- #
# OnboardingFlow: structure and decorator checks
# --------------------------------------------------------------------------- #


def test_onboarding_flow_class_exists():
    """OnboardingFlow must be importable."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "onboarding-executor" / "onboarding_flow.py"
    )
    assert hasattr(mod, "OnboardingFlow")


def test_onboarding_flow_is_a_flow():
    """OnboardingFlow must inherit from crewai Flow."""
    from crewai.flow.flow import Flow

    mod = _import_module_from_path(
        EXAMPLES_DIR / "onboarding-executor" / "onboarding_flow.py"
    )
    assert issubclass(mod.OnboardingFlow, Flow)


def test_onboarding_flow_has_expected_methods():
    """OnboardingFlow must have all the decorated methods from the article."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "onboarding-executor" / "onboarding_flow.py"
    )
    flow = mod.OnboardingFlow()
    expected_methods = [
        "onboard",            # @start
        "provision_accounts", # @listen(onboard)
        "check_result",       # @router(provision_accounts)
        "human_gate",         # @listen("approval_required")
        "escalate",           # @listen("failed")
        "send_welcome",       # @listen(human_gate)
    ]
    for method_name in expected_methods:
        assert hasattr(flow, method_name), f"Missing method: {method_name}"
        assert callable(getattr(flow, method_name)), f"{method_name} not callable"


def test_onboarding_flow_has_ask():
    """OnboardingFlow must have access to the ask() human-in-the-loop method."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "onboarding-executor" / "onboarding_flow.py"
    )
    flow = mod.OnboardingFlow()
    assert hasattr(flow, "ask"), "Flow must have ask() for human approval gates"


def test_onboarding_flow_state_management():
    """OnboardingFlow methods must use state correctly."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "onboarding-executor" / "onboarding_flow.py"
    )
    flow = mod.OnboardingFlow()
    # State should be accessible and writable
    flow.state["test_key"] = "test_value"
    assert flow.state["test_key"] == "test_value"


# --------------------------------------------------------------------------- #
# ResearchFlow: structure checks
# --------------------------------------------------------------------------- #


def test_research_flow_class_exists():
    """ResearchFlow must be importable."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "ResearchFlow")


def test_research_flow_is_a_flow():
    """ResearchFlow must inherit from crewai Flow."""
    from crewai.flow.flow import Flow

    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert issubclass(mod.ResearchFlow, Flow)


def test_research_flow_has_expected_methods():
    """ResearchFlow must have the two decorated methods from the article."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    flow = mod.ResearchFlow()
    expected_methods = ["choose_url", "summarize"]
    for method_name in expected_methods:
        assert hasattr(flow, method_name), f"Missing method: {method_name}"


def test_research_flow_allowed_domains():
    """ResearchFlow must define the allowed domains matching sandbox.yaml."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "ALLOWED_DOMAINS")
    assert "docs.example.com" in mod.ALLOWED_DOMAINS
    assert "blog.example.com" in mod.ALLOWED_DOMAINS


def test_research_flow_has_agent_factory():
    """ResearchFlow must have a deferred agent factory for the researcher."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "_create_researcher")
    assert callable(mod._create_researcher)


def test_research_flow_llm_backend_defined():
    """ResearchFlow must declare the LLM backend matching sandbox.yaml."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "LLM_BACKEND")
    assert "nim.internal" in mod.LLM_BACKEND
