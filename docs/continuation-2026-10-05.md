# Continue ResearchLens on another machine

Use remote branch **`handoff/retrieval-state-2026-10-05`**. It contains the
retrieval implementation through `0542fb8`, tracked compact experiment results,
the latest evaluation audit and four earlier research notes. The existing PR
branches and the original audit worktree are unchanged. No PR was merged.

## Get the saved state

For a new clone:

```sh
rtk git clone https://github.com/Timerk/ResearchLens.git
cd ResearchLens
rtk git switch --track origin/handoff/retrieval-state-2026-10-05
rtk proxy uv sync --locked --python 3.13
```

For an existing clone, fetch origin and switch to the handoff branch. If RTK is
not installed on the other machine, run the underlying commands without the
wrapper as described in the repository README. Install Git, uv and Python 3.13;
Node 24/npm are also needed for frontend work. Recreate virtual environments and
Node dependencies rather than copying `.venv` or `node_modules` between machines.

## Current decision and results

The best fully evaluated retrieval configuration remains BGE-M3 embeddings plus
BGE-reranker-v2-m3 over 20 candidates, returning four canonical passages. Under
the approved evidence package it scores **26/36, 72.2%**, at approximately
0.48 seconds median. TF-IDF remains the application default.

The separate thread's AI-assisted audit confirms that all 36 positive
development questions are answerable from indexed prose. Its initial proposals
would score the identical incumbent passages at **28/36, 77.8%**. These proposals
are unapproved. A separate, unresolved shortcut-scope decision would yield
29/36; it was raised after replay and must not be called a retrieval improvement.
Approved questions, evidence labels, corpus and review files are unchanged.

The previous quoted-support repair pilot fixes stripe frequencies and adaptive
binarization under the historical labels, but only stripe frequencies remains
an additional gain under the initial proposed interpretation. That is an
eight-positive/two-negative pilot, not a new full-set result. Its substantial
latency and verifier mistakes prevent adoption.

Next work is to settle a question-aligned, versioned development contract with
truthful owner approval before additional tuning. Keep historical results.
Under the initial proposals, three failures concern selection within sufficient
BGE20 candidates and five lack complete evidence in that candidate pool. The
three selection misses are glass-lighting paraphrase, fusion comparison and
stripe-frequency phase context.

Held-out questions remain reserved. The audit disclosed accidental exposure to
rejected held-out drafts, without inspecting or executing the frozen held-out
questions. Preserve that provenance; do not claim zero held-out-related exposure.

## Read these first

- [Latest evaluation audit](retrieval-evaluation-audit-2026-10-05.md).
- [Unapproved corrections](evaluation-audit-2026-10-05/proposed-revisions.json).
- [Separate shortcut adjudication](evaluation-audit-2026-10-05/post-replay-adjudication.md).
- [Audit scoring and reproduction](evaluation-audit-2026-10-05/scoring.md).
- [Selection/repair experiments](selection-diagnostics.md).
- [Embedding setup](embeddings.md) and [Vulkan setup](vulkan-reranking.md).
- [Evaluation workflow](../evaluation/README.md) and [project setup](../README.md).

[The copy manifest](continuation-artifacts-2026-10-05.json) records byte hashes
of the 23 audit/research files copied from the source worktrees. These are copies
of other threads' work, not newly authored audit findings or approval records.
Git attributes preserve copied artifact bytes and the line endings of two
existing README files whose CRLF bytes were pinned by the audit. Approved content
is unchanged; these settings avoid hash failures on a different operating system.

## What works from Git alone

After installing base Python dependencies, code development, tests, source review
and cached audit scoring require no model weights or paid APIs. Compact results
and the full latest audit replay are committed under `docs/`.

```sh
rtk proxy uv run python docs/evaluation-audit-2026-10-05/verify-audit.py
rtk proxy uv run python docs/evaluation-audit-2026-10-05/replay.py --overlay docs/evaluation-audit-2026-10-05/proposed-revisions.json --output evaluation/runs/audit-counterfactual-new.json
```

The second command is explicitly an unapproved sensitivity analysis. It uses
cached development rankings, preserves approved inputs and refuses to overwrite
an existing output. No held-out questions, model calls or answer generation are
needed. The audit scripts compute their repository root from their own path, so
they work after checkout on another machine.

## Local assets Git does not carry

- `.venv/`, including downloaded Vulkan binaries, converted reranker GGUFs and
  the local needs/support model assets.
- Hugging Face model caches outside the repository.
- `data/index.json` and generated embedding indexes.
- `evaluation/runs/`, including complete raw runs, original frozen measurement
  bundles, server logs and experimental vector artifacts.
- `.env`, API credentials, `.serena/`, frontend build output and Node dependencies.

Model downloads and index reconstruction are documented in the embedding and
Vulkan guides. Optional embedding dependencies can be installed with
`uv sync --locked --extra embeddings --extra embedding-models --python 3.13`.
Full model experiments often expect the original ignored run directories and
indexes. Transfer those directories separately if you need to resume those exact
frozen stages, or rebuild/rerun the documented prerequisites. The tracked compact
archives do not automatically recreate every ignored directory.

The Vulkan adapter currently verifies Windows and the RX 6800 specifically.
Different hardware needs an explicitly documented runtime adaptation and new
latency measurements. CPU development and embedding retrieval do not require
that GPU.

No API key is needed for retrieval or the audit. Configure local preview mode
for application checks. Credentials must remain outside Git. There are no
owned benchmark servers left running on the original machine.
