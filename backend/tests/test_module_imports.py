"""Import isolation and dependency direction for the offline toolkit."""

import ast
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
PACKAGES = ("researchlens", "researchlens_eval")
MODULES = sorted(
    ".".join(path.relative_to(BACKEND).with_suffix("").parts)
    for package in PACKAGES
    for path in (BACKEND / package).rglob("*.py")
    if path.name != "__init__.py"
)


@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_module_imports_in_fresh_interpreter(reverse):
    # Both processes start without pytest's imported project modules. Cover opposite
    # import orders without paying interpreter/library startup once per module.
    modules = list(reversed(MODULES)) if reverse else MODULES
    code = """
import importlib
import sys
assert not any(name.startswith(('researchlens.', 'researchlens_eval.')) for name in sys.modules)
for name in sys.argv[1:]:
    importlib.import_module(name)
"""
    env = {**os.environ, "PYTHONPATH": str(BACKEND)}
    result = subprocess.run(
        [sys.executable, "-c", code, *modules],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_importing_api_does_not_load_evaluation_modules():
    code = """
import sys
import researchlens.api
loaded = sorted(name for name in sys.modules if name.startswith('researchlens_eval'))
assert not loaded, loaded
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "PYTHONPATH": str(BACKEND)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def documented_cli_modules():
    repository = BACKEND.parent
    documents = [repository / "README.md", repository / "evaluation/README.md"]
    documents.extend(
        path
        for path in (repository / "docs").rglob("*.md")
        if path.name != "evaluation-refactor.md"
    )
    names = set()
    for path in documents:
        names.update(
            re.findall(
                r"python\s+-m\s+(researchlens(?:_eval)?\.[a-z_]+)",
                path.read_text(encoding="utf-8"),
            )
        )
    for name in MODULES:
        if not name.startswith("researchlens_eval."):
            continue
        implementation = BACKEND.joinpath(*name.split(".")).with_suffix(".py")
        if any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in ast.parse(implementation.read_text(encoding="utf-8")).body
        ):
            names.add(name)
    return sorted(names)


@pytest.mark.parametrize("module", documented_cli_modules())
def test_documented_and_evaluation_cli_entry_points(module):
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        env={**os.environ, "PYTHONPATH": str(BACKEND)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_reference_scorer_source_only_changed_import_location():
    from researchlens_eval import reference_evaluation

    source = Path(reference_evaluation.__file__).read_bytes().replace(b"\r\n", b"\n")
    before_relocation = source.replace(
        b"from researchlens.models import SearchHit\n\n"
        b"from researchlens_eval.evaluation_metrics import binomial_ci, exact_mcnemar\n",
        b"from researchlens.evaluation_metrics import binomial_ci, exact_mcnemar\n"
        b"from researchlens.models import SearchHit\n",
        1,
    )
    assert hashlib.sha256(before_relocation).hexdigest() == (
        "b6dc86b250a51b2bd3579ebb3c45cc86924a0deb9394aec390faa69a048f9717"
    )


def test_research_import_graph_is_acyclic_including_deferred_imports():
    modules = {name for name in MODULES if name.startswith("researchlens_eval.")}
    graph = {}
    for name in modules:
        path = BACKEND.joinpath(*name.split(".")).with_suffix(".py")
        dependencies = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                dependencies.add(node.module)
                dependencies.update(f"{node.module}.{alias.name}" for alias in node.names)
            elif isinstance(node, ast.Import):
                dependencies.update(alias.name for alias in node.names)
        graph[name] = dependencies & modules
    visited = set()

    def visit(name, stack):
        assert name not in stack, " -> ".join((*stack, name))
        if name in visited:
            return
        for dependency in sorted(graph[name]):
            visit(dependency, (*stack, name))
        visited.add(name)

    for name in sorted(graph):
        visit(name, ())


def test_code_identity_covers_extracted_modules_and_normalizes_newlines(tmp_path, monkeypatch):
    from researchlens_eval import evaluation_core

    monkeypatch.setattr(evaluation_core, "ROOT", tmp_path)
    monkeypatch.setattr(evaluation_core.subprocess, "check_output", lambda *a, **kw: "")
    package = tmp_path / "backend" / "researchlens_eval"
    package.mkdir(parents=True)
    helper = package / "scoring.py"
    helper.write_bytes(b"value = 1\r\n")
    before = evaluation_core.code_state()["evaluation_code_sha256"]
    helper.write_bytes(b"value = 1\n")
    assert evaluation_core.code_state()["evaluation_code_sha256"] == before
    helper.write_bytes(b"value = 2\n")
    changed = evaluation_core.code_state()["evaluation_code_sha256"]
    assert changed != before
    helper.rename(package / "renamed.py")
    assert evaluation_core.code_state()["evaluation_code_sha256"] != changed
