"""Assemble unapproved review proposals, without changing the approved inputs."""

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


canopy = read(OUT / "canopy-heater.json")
wafer = read(OUT / "wafer-autoencoder.json")
labels = read(ROOT / "evaluation/labels/technical-development.json")
# The daylight group combines a necessary scope fact and a conditional tunnel claim.
# Leave its scoring untouched until an explicitly narrowed group is authored.
changes = [
    change
    for change in canopy["replay_proposals"] + wafer["proposals"]
    if change["case_id"] != "tech-daylight-interference"
]
fusion = next(c for c in labels["cases"] if c["case_id"] == "tech-compare-fusion")
group = next(g for g in fusion["groups"] if g["id"] == "part-3")
span = next(s for a in group["alternatives"] for s in a if s["passage_id"] == "pmc11510794:p5:w0")
changes.append(
    {
        "id": "fusion-expanded-model-name",
        "category": "alternatives",
        "case_id": "tech-compare-fusion",
        "group_id": "part-3",
        "action": "add_alternative",
        "spans": [span],
        "confidence": "high",
        "rationale": (
            "The paper's own contributions explicitly state an attention-based dual-branch modal "
            "fusion network using feature-level fusion. This identifies ADMF-Net by its expanded "
            "name. The p40 model-name passage is redundant, not a necessary complementary fact. "
            "Both the primary comparison audit and another AI source reviewer agreed before "
            "examining outcomes."
        ),
    }
)
for change in changes:
    change["decision_kind"] = (
        "contextual-alternative"
        if change["case_id"] == "tech-adaptive-binarization"
        else "strict-alternatives"
        if change["category"] == "alternatives"
        else "question-scope"
    )
    change["review_status"] = "unreviewed"

proposal = {
    "schema_version": 1,
    "review_status": "unreviewed",
    "proposed_contract": "question-aligned-evidence-audit-draft-2026-10-05",
    "reviewer_kind": "AI-assisted; no independent human approval",
    "scope": (
        "Development-only counterfactual scoring of the identical cached rankings. Neither a new "
        "retrieval run nor answer accuracy."
    ),
    "historical_contract": (
        "The original approved 92-group evidence package and original reference-passage recall "
        "remain unchanged and are reported separately."
    ),
    "adoption_requirements": [
        "Owner reviews semantic corrections without choosing them for their score effects.",
        "Scope removals require matching versioned required-claim/qualification changes; do not "
        "merely delete an evidence group while retaining an unconditional answer claim.",
        "Retain efficiency qualifications whenever an answer claims efficiency, the architecture "
        "conflict whenever it generalizes beyond p41's account, and the proposed-versus-tested "
        "enclosure distinction whenever an enclosure is discussed.",
        "Keep necessary scientific scope and explicitly requested facts. Do not convert optional "
        "context into permission to make an inaccurate additional claim.",
        "Save a separately versioned development dataset/label bundle with new hashes and "
        "approval; preserve all historical runs. Replay every cached comparison with existing "
        "scoring, keeping the original reference recall denominator.",
        "Generated-answer and abstention quality still require a separate review. No deployment or "
        "80% generalization claim follows from this counterfactual audit.",
    ],
    "answer_rubric_changes": [
        {
            "case_id": "tech-wafer-exact",
            "change": (
                "Make required_claims[0]'s efficiency assertion optional. If made, require fixed "
                "line frequency and excluded transmission time. Core SNR changes stay mandatory."
            ),
        },
        {
            "case_id": "tech-amff-layers",
            "change": (
                "Scope the answer to the explicitly named p41/Figure8 account; retain p46 conflict "
                "as supplemental or mandatory on broader architecture assertions. Alternatively "
                "rewrite the question to explicitly request reconciliation and retain the "
                "original package."
            ),
        },
        {
            "case_id": "tech-turn-and-flip-labels",
            "change": (
                "Move the 90-degree/eightfold example to optional detail; if used, preserve its "
                "conditions. Keep joint image/label transforms and overflow handling."
            ),
        },
        {
            "case_id": "tech-manual-outline-union",
            "change": (
                "Keep manual adjustment and union contour mandatory. Treat annotation-file "
                "checking and one-view visibility explanation as supplementary."
            ),
        },
        {
            "case_id": "tech-daylight-interference",
            "change": (
                "Rubric-only proposal, excluded from executable replay changes. Keep uncontrolled "
                "ambient light, contrast loss and processing improvement in the requested answer. "
                "Make a proposed tunnel conditional on introducing containment. Before adoption, "
                "retain p34:w0 [0,151) in a narrowed core group, rather than deleting the mixed "
                "group wholesale. All facts remain in the same mandatory passage, so this cannot "
                "change full-passage completeness."
            ),
        },
        {
            "case_id": "tech-glass-paraphrase",
            "change": (
                "Remove the duplicated qualification text in a future version; no evidence-group "
                "or score change."
            ),
        },
        {
            "case_id": "comparison cases",
            "change": (
                "Do not require unsolicited common-benchmark disclaimers for descriptive "
                "comparisons. Retain the no-direct-ranking explanation for "
                "tech-compare-evaluation-metrics because that question explicitly asks it. "
                "Preserve units, patch-versus-full-image distinctions and prohibitions on "
                "unsupported claims."
            ),
        },
    ],
    "source_audit_sha256": {
        name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        for name in ("canopy-heater.json", "wafer-autoencoder.json", "comparisons-negatives.json")
    },
    "changes": changes,
}
(OUT / "proposed-revisions.json").write_text(
    json.dumps(proposal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
)
print(f"Wrote {len(changes)} proposals; approved files unchanged.")
