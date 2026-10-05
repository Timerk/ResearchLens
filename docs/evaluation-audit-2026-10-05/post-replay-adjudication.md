# Post-replay shortcut-question adjudication

This supplemental judgment is AI-assisted, exploratory and unresolved by the
owner. It was made after the main cached-result replay. The approved annotations,
the first-pass semantic audit, the 13-change proposed overlay and its replay
results remain unchanged. This record qualifies the first-pass necessity judgment
without replacing it or presenting the follow-up as an independent human review.

## What changed in the judgment

The visible question `tech-too-many-shortcuts` asks:

> In the two-stage surface-reconstruction study, why did the network avoid shortcuts between every matching layer of its encoder and decoder?

The first-pass audit treated an explanation of residual-based localization as a
necessary qualification. After the replay showed this case among the remaining
failures, the root investigator asked for another semantic judgment. Two AI
reviewers agreed that a narrower empirical explanation may answer the question:
all-layer shortcuts partly reconstructed defects, whereas two strategically placed
connections worked best in the reported experiment. The disagreement concerns
the depth of explanation required by "why". It does not concern the paper's
reported observation.

The source is [Shiferaw and Yao, section 3.1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11121878/),
canonical passage `pmc11121878:p16:w0`, XML locator
`./body/sec[3]/sec[1]/p[1]`. Two unchanged approved spans state:

> While experimenting with various skip-connection configurations, we found that utilizing two strategically placed connections yielded optimal results.

This quote occupies canonical character offsets `[1124,1274)`.

> Notably, applying skip-connections to all layers resulted in partial defect reconstruction.

This quote occupies `[1275,1366)`. Both exact quotes and offsets were revalidated.

A proposed narrow answer would be: "The authors found that two strategically
placed skip connections worked best in their experiments; connecting every layer
partly reconstructed the defects." Whether this adequately answers "why" is an
owner judgment. Requiring the next explanatory step is also defensible: why
reconstructing a defect weakens this method's detection signal.

P16, even combined with p17, does not establish the explicit claim "partial
defect reconstruction reduces residual-based discrimination." The follow-up
does not add those passages as alternatives for that unchanged claim. If an
answer makes that mechanism claim, it still needs supporting evidence. The
exploratory scope would instead treat the mechanism as conditional on making
that additional claim. Adopting this scope would require changing the associated
answer-review qualification, not just deleting a retrieval label.

## Separate cached sensitivity

[shortcut-sensitivity.py](shortcut-sensitivity.py) reuses the main replay adapters
and existing evaluator. It scores the incumbent's same four cached passages
under the approved contract, the unchanged main 13-change proposal, and a separate
in-memory removal of `residual-purpose`. It verifies the main overlay/results
hashes before and after, and records them in
[shortcut-sensitivity.json](shortcut-sensitivity.json). It does not rerun
retrieval, inspect held-out cases or generate answers.

| Contract | Complete evidence | Mean group coverage | Status |
| --- | ---: | ---: | --- |
| Original approved package | 26/36, 72.2% | 80.28% | Historical result |
| Main 13-change snapshot | 28/36, 77.8% | 83.06% | Unreviewed semantic proposals |
| Main snapshot plus narrow shortcut scope | 29/36, 80.6% | 84.44% | Post-outcome exploratory sensitivity |

Only `tech-too-many-shortcuts` changes relative to the main snapshot. P16 was
already the incumbent's first result. Original reference recall remains 71.66%,
any-evidence hit remains 33/36, and MRR remains 0.8333. The 14 negatives remain
unscored. The BGE20 oracle ceiling changes from 31 to 32, because that candidate
pool contains p16 but lacks support for the explicit residual-discrimination
requirement. The Qwen40 ceiling remains 34.

Seven cases remain incomplete under the exploratory scope:

- `tech-glass-paraphrase`
- `tech-compare-fusion`
- `tech-stripe-frequencies`
- `tech-both-checks-clean`
- `tech-moving-signal-addition`
- `tech-changing-neighborhood`
- `tech-compare-localization-outputs`

The first three are selection failures inside BGE20; the other four remain
candidate-pool failures under this scope.

This arithmetic reaches the number 29 under a different, post-outcome contract.
It does not demonstrate that retrieval met the original target, improve the
retriever, establish generated-answer accuracy or validate generalization.
The main 28/36 unreviewed sensitivity remains separately reported. The owner
should decide the intended depth of a "why" answer before adopting any revision.
If the original causal-depth expectation is retained, this case remains a
retrieval failure and the approved result remains 26/36.

Reproduce the exploratory calculation with a new output path:

```sh
rtk proxy .venv/Scripts/python.exe docs/evaluation-audit-2026-10-05/shortcut-sensitivity.py --output evaluation/runs/shortcut-sensitivity-new.json
```
