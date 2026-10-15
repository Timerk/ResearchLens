# Evaluation refactoring

Base commit: `1b0424a3aca0539a04b111137a82b11403ecc79a`.

## Evidence identity

`evaluation.code_state()` hashes a mapping from eight fixed filenames to SHA-256
digests of their LF-normalized file bytes: evaluation.py, evaluation_schema.py,
artifacts.py, evaluation_memory.py, evaluation_evidence.py, evaluation_metrics.py,
answers.py, and models.py. It also records the Git commit and dirty flag. The base
evaluation code digest is
`5a9a67b86cee96fe0558fc46116c62edd0d2e91baa52df469f0e1fde5031f386`.

`answer_judge_freeze.current_contract()` compares the whole judge contract. It
includes the LF-normalized bytes of answer_judge_v2.py, the concatenated
`inspect.getsource(score)` and `inspect.getsource(all_decided)`, prompt hashes,
the Judgment JSON schema, and settings. Function locations are not hashed.

`reference_evaluation` records its own complete LF-normalized source digest.
Evidence manifests also pin raw file/archive SHA-256 and canonical JSON digests.
`canonical_hash` uses sorted-key JSON, UTF-8, ensure_ascii=False, allow_nan=False.
Source hashes normalize CRLF; arbitrary archive/file hashes do not.

Historical files under evaluation/ and docs/ remain unchanged. No paid study,
held-out retrieval, or evidence regeneration is part of this work. The user
authorized a new code identity for Phase 2. This does not authorize changing the
judge freeze or rewriting historical run identities.

## Phase 1

Branch: `refactor/answer-execute-phase1`.

Characterization tests passed against the original executor before extraction.
They cover reservation and checkpoint ordering, both provider failure stages,
cancellation, unresolved generation checkpoints, and recovery from a newer
checkpoint containing a completed judgment. Additional tests cover missing
sources, reordered sources, and exhausted per-call reservations.

Configurations resolve by name through the approved plan's ranking digest,
rather than the position of a run in the supplied list. Missing sources fail
before client creation or output writes. Reservations, persisted receipts,
checkpoint ordering, error termination, and resume behavior are preserved.

Function lengths include signatures and blank lines, measured with Python AST:
execute 260 -> 75; configuration_setup 67; replay_checkpoint 13; execute_case 139.
Other large functions are unchanged: evaluation.run_evaluation 316,
evaluation.main 189, evaluation.summarize 160, evaluation.comparison_report 127.

Imports are unchanged in this phase. Existing deferred-import cycles include
evaluation <-> answer_evaluation, answer_evaluation <-> answer_judge_experiment,
answer_evaluation <-> answer_judge_freeze, and answer_evaluation <-> answer_parallel.

Validation: Ruff lint and format checks pass; 297 passed, 3 skipped. Coverage is
2460/3271 statements (75.21%), above the baseline 2416/3238 (74.61%). The committed
freeze passes and all previously hashed source files retain their bytes.

## Phase 2

Branch: `refactor/evaluation-cycles-phase2`, based on Phase 1.

The research graph is now acyclic, including deferred imports. The CLI depends
on answer execution, the retrieval runner, and reporting. Execution depends on
scoring, reporting, the runner, parallel scheduling, and judge experiments.
Experiments depend on grading, freeze verification, and scoring. Reporting and
the runner depend on evaluation_core, evidence, metrics, and schema. None of
those lower layers imports a command or execution module. Parallel scheduling
receives its worker callback from the caller.

Shared source validation and provenance are in evaluation_core; retrieval
execution is in evaluation_runner; review/report code is in evaluation_reporting.
Answer models, scoring, context selection and reservation accounting are in
answer_scoring; answer reports are in answer_reporting. Existing public imports
are re-exported. Tests that patched moved definitions now patch their definition
sites. Research imports formerly deferred to avoid cycles are at module scope.
The local citation_value import inside score is deliberately preserved because
it is part of the source-pinned function; it points to a dependency leaf.

The authorized new code identity hashes relative paths and LF-normalized bytes
for every Python source under backend/researchlens and backend/researchlens_eval.
This includes extracted helpers and future compatibility entry points. Historical
run identities remain historical; their manifests are not rewritten.

Shared serving defaults name the model, answer output cap and context character
limit. Study constants name the case count, generation/judge limits, and framing
allowance. Frozen judge literals, the source-pinned reference scorer, JSON schema
Literal values, and unrelated limits with coincidentally equal numbers remain.

Validation: Ruff lint and format checks pass; 337 passed, 3 skipped. Coverage is
2546/3350 statements (76.00%). Fresh-interpreter imports cover every module; an
AST graph test also rejects deferred research cycles. The freeze still passes.
The reference scorer source digest remains
`b6dc86b250a51b2bd3579ebb3c45cc86924a0deb9394aec390faa69a048f9717`;
the judge source digest remains
`be179202e3df3ad8a3d6d5b24c8eccb15d92399352f0ae78978b075e12424b2f`.
No historical evaluation/ or docs/ file changed.

Largest functions retain their behavior and lengths: run_evaluation 316,
summarize 160, comparison_report 127. The CLI main is 188 lines, execute 71,
and execute_case 138 after removing deferred imports.

## Phase 3

Branch: `refactor/evaluation-package-phase3`, based on Phase 2.

The 22 research modules now live in the sibling package researchlens_eval.
The old paths contain compatibility modules. Imports return the same module
objects, preserving class identity and existing monkeypatch behavior. Modules
with a main function also forward their old `python -m researchlens.*` entry
points. The README, docs/, and evaluation/README.md commands were searched;
their help commands are covered by tests. The documented `uv run --directory
backend python -m researchlens.evaluation --help` invocation also passed.

The frozen judge and reference scorer were copied with their source bytes
unchanged. The reference scorer continues to read its actual implementation
file, so its recorded source hash is preserved. The two frozen scoring functions
also retain their exact source text, including their local legacy import. The
compatibility import resolves to the same judge implementation. assert_frozen
passes after the move. No freeze or historical manifest was regenerated.

The research graph retains Phase 2's acyclic dependency direction. Compatibility
modules point into researchlens_eval. The reference scorer and frozen score
retain legacy imports pointing through compatibility modules to dependency
leaves. Serving modules have no dependency on either research implementations
or their compatibility modules. A fresh-interpreter test imports researchlens.api
and checks sys.modules for both kinds of evaluation module.

```text
Before: evaluation <-> answer_evaluation <-> judge experiment / freeze / parallel

After:  legacy entry points -> researchlens_eval CLI / execution
        CLI / execution -> runner / reporting / experiments / parallel
        experiments -> grading / freeze -> scoring
        runner / reporting -> core / evidence / metrics / schema
        research toolkit -> serving primitives
        API -> serving primitives
```

Final function lengths: execute 71, configuration_setup 65, replay_checkpoint 13,
execute_case 138. Other large functions: run_evaluation 316, CLI main 188,
summarize 160, comparison_report 127. The unchanged large retrieval/reporting
functions were outside the requested execute refactor.

Validation: Ruff lint and format checks pass; 391 passed, 3 skipped. Coverage
includes both namespaces using `--cov=researchlens --cov=researchlens_eval`,
so the package move does not hide research code from measurement. Combined
coverage is 2618/3428 statements (76.37%). The implementation statement counts
and misses match Phase 2; compatibility modules add 78 statements and 6 misses.
Every module imports in a fresh interpreter, legacy module identities match,
and the static research graph is acyclic, including deferred imports.

Phase 3 source identity before integration with main:
`7c3b66af74b427416c249072f49b6da33b4b1a5f00cd1b251c4b5e540cae2c40`.
This intentionally differs from the original eight-file identity. The original
identity remains in historical evidence, tied to its original commit.

Deliberately unchanged: historical evaluation/ and docs/ files; frozen judge
source, scoring function source, and reference scorer source; study values;
optional serving-model imports; unrelated numeric limits. No paid calls,
held-out retrieval, evidence reruns, pushes, or PRs were performed.

## Integration with current main for PR #48

Merged main at `f142a0f` rather than rebasing the three reviewed phase commits.
Main's atomic writer, context caps/minimum budget/422 handling, encoder lock,
dependency updates, and four-job CI configuration are retained. In particular,
api.py, artifacts.py and embedding_models.py have no diff from current main.
There are no changes under evaluation/ relative to main or the original base.

The serving answers.py retains main's complete behavior. Its only differences
from main are importing ANSWER_OUTPUT_TOKENS and using it for the unchanged
2000-token cap. config.py retains main's minimum-context validation and error
message; its differences are named model and tier-context defaults. The sole
mutable-code definition of the 16000-character ceiling is now MAX_CONTEXT_CHARS
in context_limits.py. defaults.DEFAULT_CONTEXT_CHARS aliases that value.
The source-pinned reference scorer necessarily retains its original literal.

### Current-main moved-module audit

Each existing old module was diffed against
`origin/main:backend/researchlens/<name>.py` at `f142a0f`. For the two split
modules, every original function and class was also located in its destination
and compared as an AST. After normalizing imports and the unchanged values of
named constants, all definitions match except execute and code_state. The
parallel callback signature change is accounted for separately below.

| Destination in researchlens_eval | Differences from current main beyond relocation |
| --- | --- |
| answer_constants.py | New extraction of study case count, framing allowance, generation cap, and judge cap; values unchanged. Context ceiling aliases serving defaults. |
| answer_evaluation.py | Scoring and reports extracted and re-exported; safe imports moved to module scope. execute decomposed into configuration/replay/case helpers and state dataclasses. Sources resolved by approved ranking digest under configuration names and validated before client construction. Generation also checks cancellation immediately before reservation. All other original definitions match after import/constant normalization. |
| answer_grading.py | Imports scoring/schema from their lower layers; import ordering only. |
| answer_judge_experiment.py | Imports scoring/schema from lower layers; tiktoken and freeze verification imports moved to module scope; import ordering and wrapping only. Function bodies otherwise match. |
| answer_judge_freeze.py | Scoring/model/review imports relocated. The atomic_write_text call and every function body match current main. |
| answer_judge_review.py | Grading import relocated only. |
| answer_judge_v2.py | Identical source, including recorded LF-normalized bytes. |
| answer_parallel.py | Save and spot-check imports use lower layers. execute_parallel receives the execute callback explicitly instead of importing the command module. Scheduling, assignments, stop propagation, merge, and resume logic otherwise match. |
| answer_reporting.py | Extracted METRICS, quality_report, spot_check_template, and reliability; named case count and safe module-level comparison-report import; calculations unchanged. |
| answer_scoring.py | Extracted scoring/models/context/reservation helpers. save exactly matches main's atomic writer. Context ceiling uses the shared alias. score and all_decided retain exact source text. |
| answer_study_budget.py | Identical normalized source to main, including atomic_write_text for StudyBudget.write. |
| compare_retrieval.py | Toolkit imports relocated and reordered only; subprocess commands retain legacy CLI paths. |
| context_evaluation.py | Imports relocated; context ceiling named without changing its value; tiktoken import at module scope. All function bodies otherwise match. |
| evaluation.py | Validation, runner, provenance, and reporting extracted and re-exported. Answer command imports at module scope. CLI body matches after import normalization. |
| evaluation_core.py | Extracted digest/encoding/dataset/reference validation. code_state intentionally hashes relative paths and LF-normalized bytes across both complete packages instead of eight old filenames. |
| evaluation_evidence.py | Schema import relocated; import ordering only. |
| evaluation_memory.py | Identical normalized source. |
| evaluation_metrics.py | Identical normalized source. |
| evaluation_reporting.py | Extracted review_template, summarize, comparison_report, and their imports; definitions match. |
| evaluation_runner.py | Extracted Search, encoding configuration, installed versions, and retrieval runner. Named model constant. run_evaluation matches main, including passing only provider.context_chars and context_mode to prepare_answer_context; shared passage limits come from its defaults. |
| evaluation_schema.py | Named model and output-cap constants, with identical values and schema; serving-model import retained. |
| reference_evaluation.py | Identical source; recorded source digest unchanged. |

The new package __init__.py contains only its descriptive docstring. Legacy
researchlens modules are import aliases and CLI forwarding entry points. They
retain module/class identity. None is imported by the serving API. No other
implementation differences were found in the moved modules.

### Integrated validation

The main-provided test_atomic_evaluation_state.py and test_context_budget.py
run in full. Added two temporary-file tests verify freeze publication, refusal
to overwrite, and cleanup when atomic replacement fails. They do not touch the
committed freeze.

The import check now uses two fresh interpreters, importing every module in
forward and reverse order, instead of starting a process per module. Each
process checks that no project modules were already loaded. The static graph
check still inspects deferred imports. Separate fresh-process API isolation and
CLI checks remain.

On this Windows/Python 3.14 machine, the integrated full suite took 76.60 seconds
before optimization and 27.16 seconds afterwards. The latter includes the two
additional freeze tests. Test counts changed because imports are now grouped:
431 passed / 6 skipped before, 374 passed / 6 skipped after. Coverage measured
both packages at 2672/3471 statements, 76.98%, above the unchanged 75% CI floor.
Ruff lint and format checks passed.

The integrated source identity is
`8d1fc137ce6b3968f73871ce0ac5cd675311776f494de58599c724be9e746c17`.
assert_frozen passes, both frozen scoring function sources exactly match main,
and the frozen judge/reference scorer digests above remain unchanged. The
retrieval runner is now 314 lines after porting main's shared-context call.
CI measures both packages with
`--cov=researchlens --cov=researchlens_eval --cov-fail-under=75`.
