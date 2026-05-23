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
    module_name = f"test_import_{path.stem}_{id(path)}"
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
    """ResearchFlow must have the decorated methods for competitive research."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    flow = mod.ResearchFlow()
    expected_methods = ["choose_url", "scout_company", "find_competitors"]
    for method_name in expected_methods:
        assert hasattr(flow, method_name), f"Missing method: {method_name}"


def test_research_flow_allowed_domains():
    """ResearchFlow must define allowed target domains."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "ALLOWED_DOMAINS")
    assert "spillwave.ai" in mod.ALLOWED_DOMAINS


def test_research_flow_has_agent_factories():
    """ResearchFlow must have deferred agent factories."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "_create_scout"), "Missing _create_scout"
    assert hasattr(mod, "_create_competitor_finder"), "Missing _create_competitor_finder"
    # Both should use SerperDevTool, not ScrapeWebsiteTool
    content = (EXAMPLES_DIR / "research-assistant" / "flow.py").read_text()
    assert "ScrapeWebsiteTool" not in content, "Should use SerperDevTool, not ScrapeWebsiteTool"


def test_research_flow_has_csv_config():
    """ResearchFlow must define CSV output columns."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "CSV_COLUMNS")
    assert "url" in mod.CSV_COLUMNS
    assert "name" in mod.CSV_COLUMNS
    assert "competitive_overlap" in mod.CSV_COLUMNS
    assert "description" in mod.CSV_COLUMNS


def test_research_flow_uses_json_output():
    """ResearchFlow must parse JSON (not raw CSV) from LLM for reliable output."""
    content = (EXAMPLES_DIR / "research-assistant" / "flow.py").read_text()
    assert "json.loads" in content, (
        "flow.py should use json.loads to parse structured LLM output"
    )


def test_research_flow_has_llm_factory():
    """ResearchFlow must have a _get_llm factory for inference.local routing."""
    mod = _import_module_from_path(
        EXAMPLES_DIR / "research-assistant" / "flow.py"
    )
    assert hasattr(mod, "_get_llm")
    assert callable(mod._get_llm)
