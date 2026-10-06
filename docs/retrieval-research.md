# Retrieval research

The application supports TF-IDF, pinned CPU embeddings, weighted hybrid fusion and
optional MiniLM CPU reranking. TF-IDF remains the default. See
[embedding setup](embeddings.md) for installation and supported configuration.

The studies below are development experiments. Vulkan reranking, information-needs
extraction, contextual representations, constrained selection and support repair
are evaluation tools rather than application settings. The configuration files
named `development-selected-*` record study selections; startup does not load them.

| Study | What it establishes |
| --- | --- |
| [Approved CPU comparison](approved-model-comparison.md) | Nine configurations on all 50 approved development cases. |
| [Retrieval improvements](retrieval-improvements.md) | Weighted fusion, MiniLM reranking, diversity and visibility measurements. |
| [Vulkan reranking](vulkan-reranking.md) | Experimental GPU backend, reference checks, quality and latency. |
| [Complementary selection](complementary-selection.md) | Query splitting and metadata reranking; tested variants regress. |
| [Information needs](information-needs-experiments.md) | Fixed-pool selectors and contextual vectors; no better study winner. |
| [Selection diagnostics](selection-diagnostics.md) | Candidate ceilings, label-assisted diagnostics and a slow repair pilot. |
| [Historical CPU comparison](model-comparison.md) | Earlier draft-label results; not comparable with approved-label scores. |

## Result archives

Checked-in result JSON files contain summaries with protocol, provenance, scores,
cohorts and cost measurements. Repeated per-case scoring, inference matrices and
passage/group details remain in full archives. Each summary's `archive_provenance`
records the full archive hash and an immutable Git link to the original version.
This preserves auditability while keeping the PR and future documentation readable.

Generated runs, vectors, weights and logs belong in ignored `evaluation/runs/` or
the model cache. [Research utilities](../evaluation/scripts/README.md) extract
archives and create summaries without changing the shared scoring framework.

## Remaining work

The five retrieval targets have not all been reached. These small, correlated
four-paper development studies also do not establish held-out quality,
generated-answer correctness, citation support or abstention behavior.

Performance optimization is postponed until the stronger machine is available.
Keep the current approved datasets, labels and source texts fixed for comparisons.
The later CPU investigation and its application-integration prototypes are outside
this PR. Resume them in a separate performance PR, verify backend parity and fresh
application inference, then evaluate frozen settings on held-out data.
