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
| [Serialized context budgets](context-budget.md) | Qwen dense at 12k/16k characters meets all five development retrieval targets; answer quality remains unmeasured. |
| [Historical CPU comparison](model-comparison.md) | Earlier draft-label results; not comparable with approved-label scores. |

## Result archives

Checked-in result JSON files contain summaries with protocol, provenance, scores,
cohorts and cost measurements. Repeated per-case scoring, inference matrices and
passage/group details remain in full archives. Each summary's `archive_provenance`
records the full archive hash and its recovery location. Historical summaries also
link to their original full versions in Git.
This preserves auditability while keeping the PR and future documentation readable.

Generated runs, vectors, weights and logs belong in ignored `evaluation/runs/` or
the model cache. [Research utilities](../evaluation/scripts/README.md) extract
archives and create summaries without changing the shared scoring framework.

## Remaining work

Measured on the supplied answer context, Qwen dense meets all five development
retrieval targets at 12k and 16k serialized characters; see the
[context budget study](context-budget.md). The application default remains four
passages until answer quality with larger contexts is measured. These small,
correlated four-paper development studies do not establish held-out quality,
generated-answer correctness, citation support or abstention behavior.

Separate follow-up PRs cover hardware-dependent model tiers with a startup memory
check (Qwen3-4B peaks at about 8 GiB of RAM), readable formula rendering in the
corpus, held-out confirmation of the frozen settings and answer-quality evaluation.

Performance optimization is postponed until the stronger machine is available.
Keep the current approved datasets, labels and source texts fixed for comparisons.
The later CPU investigation and its application-integration prototypes are outside
this PR. Resume them in a separate performance PR, verify backend parity and fresh
application inference, then evaluate frozen settings on held-out data.
