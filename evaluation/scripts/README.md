# Research utilities

Run these scripts from the repository root. They are manual development tools;
application startup does not execute them. CPU/GPU parity checks need pinned cached
models and existing development runs, as documented in the linked studies.

| Script | Purpose |
| --- | --- |
| `selection-results.py` | Extract existing runner scores and selection diagnostics. |
| `information-needs-results.py` | Extract fixed-pool and representation study results. |
| `selection-diagnostics-results.py` | Extract constrained-selection and repair diagnostics. |
| `embedding-parity-check.py` | Compare cached Qwen embeddings with reference pooling. |
| `vulkan-reference-check.py` | Compare cached CPU reranker rankings with saved Vulkan results. |
| `compact_results.py` | Reduce a full research archive to a summary for Git. |

Use fresh output paths under `evaluation/runs/` for full records. The archive
extractors preserve existing output files. The parity checks run local inference;
they are optional and are not part of application installation or normal CI.

To publish a summary after extracting a full archive:

```sh
python evaluation/scripts/compact_results.py evaluation/runs/full-results.json docs/study-results.json
```

The summary keeps manifests, model/runtime pins, hashes, aggregate scores, cohort
counts, timing/memory summaries and paired outcome counts. It records the original
archive SHA-256 and omits repeated case-level scoring, passage lists and inference
matrices. It is a research summary, not an input to the evaluation runner.

The historical JSON files in `docs/` include immutable links to their full versions
at commit `0542fb8aa1ac87b96d0e6b91320a48e2f4328889`. Those Git blob bytes match
`archive_provenance.full_archive_sha256`; Windows checkout line endings may differ.
Full local copies also remain under
`evaluation/runs/pr9-pre-cleanup-0542fb8/git-blobs/` on the investigation machine.

See [the research index](../../docs/retrieval-research.md) for protocols and limitations.
