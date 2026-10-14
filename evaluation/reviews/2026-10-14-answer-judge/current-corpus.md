# Current-corpus development answers

Step 5 completed all 250 question/configuration evaluations, with 249 generation
calls and 155 judge calls. TF-IDF has one safe no-match response without a paid
generation call. There were no provider/scoring errors or paid retries.
All five configurations use the frozen judge, the unchanged generation prompt
and today's approved readable-formula corpus, dataset and labels.

The three ranking archives are the development-only PR #15 adoption runs. The
guarded planner validates every recorded canonical hit and the complete dataset,
labels, corpus and passage-identity contract against current inputs. No embedding
or held-out retrieval was repeated. All answers themselves were generated anew.

Plan hash:
`fb6d83871e1c67f5bb91f496cb7d296d92eb41be419c080da7773ae529f1c951`.
The conservative run reservation is $2.9711926. The shared study ledger enforces
the $3 total cap across calibration, validation and generation before each call,
and reconciles only API-reported usage. Every call's usage is known.
Total Phase 2 cost at the supplied uncached rates is $0.2469009 over 449 calls.
The generation comparison alone costs $0.2105484. These are token-usage costs
at owner-supplied rates, not an independently verified billing total.

| Configuration | Complete required claims /36 | False abstentions /36 | Correct generated negative abstentions /14 |
| --- | --- | --- | --- |
| TF-IDF, four passages | 19 | 14 | 13 |
| Qwen3-4B, four passages | 26 | 7 | 14 |
| Qwen3-4B, 12k | 27 | 3 | 14 |
| Qwen3-4B, 16k | 32 | 1 | 14 |
| BGE-M3, 16k | 32 | 0 | 14 |

There are no unknown required-claim outcomes. All 36 answerable pairs enter the
pre-registered primary Qwen 12k-versus-four comparison: four gains, three losses,
23 complete in both and six incomplete in both. Two-sided exact McNemar p=1.0.
All five configurations retain every negative's status expectation except the
TF-IDF no-match, which is not a generated section-free abstention.

`docs/answer-quality-current-results.json` reports paired comparisons only for
the reliable required-claim and negative-abstention metrics. Qualifications,
citations and forbidden claims remain uncertified diagnostics, explicitly
separated from decision evidence. No composite is used. One Qwen 16k citation
receipt is unresolved; its required-claim outcome is still decidable.
These are curated development results, not held-out confirmation or a causal
estimate of formula rendering's benefit over the previous study.

The local compressed bundle preserves full runs and raw receipts. The compact
`phase2-evidence-manifest.json` records its hash and the plan, shared ledger and
review prediction hashes. Raw calibration and validation receipts remain under
ignored `evaluation/runs/phase2/`. The sealed human validation grades remain in
the common Git directory. Original datasets, labels and corpus are unchanged.

Decision application belongs to the next commit, after this result is recorded.
