# Development evidence labels

`technical-development.json` contains 92 draft evidence groups for the 36 answerable
development questions. Both approved datasets and their review records are unchanged.
The labels are AI-authored and unreviewed. They are not included in the project owner's
prior question approval. No held-out evidence labels, retrieval results or rankings
were used to create them.

The [AI evidence audit](../reviews/2026-10-01-pr8/evidence-review.md) reviewed the
original 83 groups and identified semantic/context fixes. The
[fix record](../reviews/2026-10-01-pr8/evidence-fixes.md) records the source checks,
changes and decisions on all 41 recommendations. The revised labels contain 140
alternatives and 165 exact span occurrences. Both audit files remain unchanged.
These corrections do not constitute human approval.

The draft uses exact sentences or sentence fragments from the pinned extracted
passages. Alternatives are conservative and incomplete. Some facts need complementary
spans, including spans within the same passage. A complete match certifies only that
these labeled text spans survived retrieval/context budgets. Human review must still
check factual sufficiency, qualifications, full sources and acceptable alternatives.

## Evidence format and review

The allowlisted schema is `EvidenceLabels.model_json_schema()` in
`backend/researchlens/evaluation_evidence.py`. Pins use the runner's canonical
serialized dataset hash, raw corpus hash and shared passage hash, not a model-specific
vector artifact hash. The file has its own review status, reviewer and date.

Each case has groups with a unique ID, required claim index and factual description.
Every required claim needs at least one group. Composite claims may need several
groups. Alternatives are lists of supporting spans:

Source-supported factual qualifications can form required groups associated with the
claim they qualify. These include fixed-line-frequency bounds, an incomplete-noise
correction and conflicting architecture prose. Generic limits on generalization,
unreported numerical values, forbidden claims and reasoned non-comparability remain
answer-review rules. Passage retention does not establish compliance with those rules.

```json
{
  "id": "illumination",
  "claim_index": 0,
  "description": "Example evidence requirement",
  "alternatives": [
    [{"passage_id": "P1", "start": 10, "end": 25, "quote": "exact text here"}],
    [
      {"passage_id": "P2", "start": 0, "end": 15, "quote": "exact text here"},
      {"passage_id": "P3", "start": 0, "end": 15, "quote": "exact text here"}
    ]
  ]
}
```

This schematic example means P1 OR the combination P2 AND P3. Real labels must use
existing pinned passage IDs, exact quotes and half-open Unicode character offsets.
New alternatives can reference passages outside the original question reference list,
but must belong to one of its expected source documents. Duplicate groups, spans,
alternatives, missing claim indices and stale quotes fail validation.

When reviewing:

- Check each group against the required claims and qualifications. Split composite
  requirements until missing one fact produces incomplete evidence.
- Check that every alternative alone supplies that group, including all necessary
  conditions and qualifications. A nearby paragraph or shared keyword is insufficient.
- Check complementary evidence together, with each span required for the fact.
- Confirm offsets and quotes against the pinned extracted passage, and factual support
  against the full source. Do not invent offsets for unextracted tables or figures.
- Add omitted valid alternatives. Avoid interpreting reference-list passage recall
  as a claim-support score.
- Preserve all negative cases as unscored. Their context references are not support.

Set this file to `approved` with truthful reviewer/date only after that review. Its
hash changes, so rerun all compared development modes. Do not relabel held-out cases
after inspecting model failures. Do not alter the existing human approval archive.

## Encoder measurement format

Adapters can return this strict sidecar through `get_encoding_diagnostics()` or a
user can pass it with `--encoding-diagnostics`. Values below are schematic placeholders,
not measurements. Hash fields in a real file must be lowercase 64-character SHA-256:

```json
{
  "schema_version": 1,
  "artifact_sha256": "canonical_hash(full_embedding_artifact)",
  "encoding_sha256": "canonical_hash(artifact.embeddings.encoding)",
  "token_count_scope": "encoder-input-including-instructions-and-special-tokens",
  "passages": [
    {
      "passage_id": "existing-passage-id",
      "text_sha256": "sha256(canonical_passage_text_utf8)",
      "input_tokens": 310,
      "encoded_tokens": 256,
      "truncated": true,
      "retained_ranges": [{"start": 0, "end": 900}]
    }
  ]
}
```

The retrieval adapter must measure tokens with its pinned tokenizer, instructions,
special tokens and actual truncation settings. Ranges refer only to canonical
passage text, include intervening whitespace, and must be ordered and nonoverlapping.
For a full untruncated passage, retain `[0, len(text))`. A truncated passage can have
no retained text, such as when instructions consume the budget. Missing measurements
remain unknown. Never fabricate token counts or infer retention from model names.

`canonical_hash` is the shared helper in `researchlens.artifacts`. It hashes sorted-key
JSON with `ensure_ascii=False`, `allow_nan=False` and default separators. Passage text
hashes use its exact UTF-8 bytes. This differs from a file-byte hash.

The evaluator validates these records without implementing tokenization or embeddings.
It reports corpus truncation rates over measured passages only and exposes unknown
counts. Evidence groups lost from the encoded portion are separate from retrieval
misses and the answer provider's context selection/truncation losses. For hybrid
retrieval, encoder visibility describes only its embedding component.
