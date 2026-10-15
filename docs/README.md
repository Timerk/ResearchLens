# Documentation index

Start with [results.md](results.md), which tells the evaluation story in order and
links to each detailed document below.

## Guides

| Document | Contents |
| --- | --- |
| [results.md](results.md) | One-page summary of every study, in order |
| [docker.md](docker.md) | Docker Compose setup, tier switching and the fresh-clone check |
| [development.md](development.md) | Local setup without Docker, OpenAI mode, corpus, tests and code layout |
| [embeddings.md](embeddings.md) | Embedding models, encoding contract, hardware tiers and hybrid retrieval |

## Results

These are the current, committed measurements.

| Document | Contents |
| --- | --- |
| [formula-adoption-results.md](formula-adoption-results.md) | Development retrieval on the adopted readable-formula corpus |
| [formula-adoption-results.json](formula-adoption-results.json) | Machine-readable version, with pins and hashes |
| [held-out-results.md](held-out-results.md) | One-time held-out retrieval confirmation |
| [held-out-results.json](held-out-results.json) | Estimates, intervals, paired tests and provenance |
| [answer-quality.md](answer-quality.md) | Generated answer quality, judge validation and the context decision |
| [answer-quality-current-results.json](answer-quality-current-results.json) | Current-corpus answer metrics from the frozen judge |
| [context-budget.md](context-budget.md) | Character-budgeted context study, current and historical |

## Methodology and decisions

These documents record protocols, reviews and the configuration pins chosen on the
development set.

| Document | Contents |
| --- | --- |
| [held-out-preregistration.md](held-out-preregistration.md) | Held-out protocol, committed before any held-out search |
| [formula-rendering-proposal.md](formula-rendering-proposal.md) | Readable MathML extraction, approved and adopted |
| [formula-remapping-review.md](formula-remapping-review.md) | Evidence span and reference remapping, reviewed by the owner |
| [development-selected-retrieval.json](development-selected-retrieval.json) | Pinned retrieval configuration selected on development |
| [development-selected-context-budget.json](development-selected-context-budget.json) | Pinned context budget selected on development |

The evaluation workflow, datasets and review records live in
[`evaluation/`](../evaluation/README.md).

## Historical and archived research

These documents describe earlier corpora or experiments. Newer results above
supersede their numbers.

| Document | Contents |
| --- | --- |
| [retrieval-research.md](retrieval-research.md) | Index of the archived retrieval experiments in the `research/retrieval-2026-10` tag |
| [formula-rendering-results.md](formula-rendering-results.md) | Phase-1 formula intervention measurements, before approval |
| [formula-rendering-results.json](formula-rendering-results.json) | Machine-readable phase-1 results |
| [answer-quality-results.json](answer-quality-results.json) | 2026-10-13 answer-quality study on the pre-formula corpus |
| [quantized-embedding-feasibility.md](quantized-embedding-feasibility.md) | Plan for a possible GGUF Qwen3-4B tier, not implemented |
