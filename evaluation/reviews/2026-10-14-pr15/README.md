# Owner-approved formula corpus adoption

The project owner reviewed `docs/formula-remapping-review.md` and approved every
proposed development span mapping and held-out reference change on 2026-10-14.
The reason is "source text change from formula rendering". [approval.json](approval.json)
records the statement, reviewer, date, previous/candidate/adopted pins and all groups.

The 165 original span occurrences classify as 132 unchanged, 14 shifted only and
19 changed quotes. None is unmappable. Two required AND splits give 167 current
fragments. All 92 groups and 140 alternatives are preserved.

Held-out has references only. Its 62 previous occurrences include seven text changes
and four window-ID splits. The new frozen version has 66 references. This migration
comes from offline corpus alignment, not held-out model results. Questions, answers,
claims and source versions are preserved. No held-out retrieval or answer inspection ran.

The `datasets/` and `labels/` snapshots preserve previous approved files byte-for-byte.
The original reviewed remapping, phase-1 results and prior retrieval selections are
also preserved here. The 2026-10-01 approval records and 2026-10-13 paid answer-quality
evidence retain their original hashes. None was relabeled as a new experiment.

The adopted corpus differs from the reviewed candidate only in attribution wording
that records approval; every document's rendered text is identical. All four
application tier indexes were rebuilt. [Current results](../../../docs/formula-adoption-results.md)
confirm Qwen meets all five development targets at 12k and 16k. No paid API calls ran.
