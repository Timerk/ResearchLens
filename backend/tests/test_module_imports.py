"""Import isolation and dependency direction for the offline toolkit."""

import ast
import hashlib
import importlib
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
LEGACY_MODULES = [
    name
    for name in MODULES
    if name.startswith("researchlens.")
    and BACKEND.joinpath("researchlens_eval", name.split(".")[-1] + ".py").exists()
]


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


@pytest.mark.parametrize("module", LEGACY_MODULES)
def test_legacy_imports_share_module_identity(module):
    assert importlib.import_module(module) is importlib.import_module(
        module.replace("researchlens.", "researchlens_eval.", 1)
    )


def test_importing_api_does_not_load_evaluation_modules():
    code = """
import sys
import researchlens.api
legacy_modules = set(sys.argv[1:])
loaded = sorted(name for name in sys.modules
                if name.startswith('researchlens_eval') or name in legacy_modules)
assert not loaded, loaded
"""
    result = subprocess.run(
        [sys.executable, "-c", code, *LEGACY_MODULES],
        env={**os.environ, "PYTHONPATH": str(BACKEND)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def documented_cli_modules():
    repository = BACKEND.parent
    documents = [repository / "README.md", repository / "evaluation/README.md"]
    documents.extend((repository / "docs").rglob("*.md"))
    names = set()
    for path in documents:
        names.update(
            re.findall(r"python\s+-m\s+(researchlens\.[a-z_]+)", path.read_text(encoding="utf-8"))
        )
    for name in LEGACY_MODULES:
        implementation = BACKEND / "researchlens_eval" / (name.split(".")[-1] + ".py")
        if any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in ast.parse(implementation.read_text(encoding="utf-8")).body
        ):
            names.add(name)
    return sorted(names)


@pytest.mark.parametrize("module", documented_cli_modules())
def test_documented_and_legacy_cli_entry_points(module):
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        env={**os.environ, "PYTHONPATH": str(BACKEND)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_reference_scorer_preserves_recorded_source_digest():
    from researchlens_eval import reference_evaluation

    source = Path(reference_evaluation.__file__).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(source).hexdigest() == (
        "b6dc86b250a51b2bd3579ebb3c45cc86924a0deb9394aec390faa69a048f9717"
    )


def test_research_import_graph_is_acyclic_including_deferred_imports():
    modules = {
        name
        for name in MODULES
        if name.startswith("researchlens_eval.")
        or name.rsplit(".", 1)[-1].startswith(
            (
                "answer_",
                "evaluation",
                "context_evaluation",
                "reference_evaluation",
                "compare_retrieval",
            )
        )
    }
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
    from researchlens import evaluation_core

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
