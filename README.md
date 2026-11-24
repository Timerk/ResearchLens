# ResearchLens

[![CI](https://github.com/Timerk/ResearchLens/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Timerk/ResearchLens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Corpus: CC BY 4.0](https://img.shields.io/badge/corpus-CC%20BY%204.0-lightgrey.svg)](data/technical/NOTICE.txt)

ResearchLens answers questions about technical papers using only the papers' own text.
Each part of an answer cites the passages it came from, and each citation opens to
show the source section, XML location, authors and license. When the passages do not
support an answer, it returns an explicit insufficient-evidence response. It is built
for engineers and researchers who need to check where a claim comes from. The bundled
corpus is four open-access CC BY 4.0 papers on optical defect inspection. The retrieval and answer pipeline was evaluated
with owner-approved questions, a held-out set run once, and pre-registered decision
rules.

**Live demo:** <https://204-168-204-171.sslip.io>. See [Try it](#try-it)
for recorded examples and live-answer limits.

![Desktop view: a recorded answer replayed on the question page, with its first citation expanded](docs/images/desktop-answer.png)

*A recorded answer replayed on the question page with its first citation open. `gpt-6-luna`
wrote it during the 2026-10-13 development evaluation run (`answer-quality-2026-10-13`,
case `tech-wafer-exact`, Qwen3-4B retrieval with 12,000 context characters); the
backend replays the saved run, so no API call was made. The stack ran locally without an
API key, which is why the header shows local preview.
More screenshots: [landing page](docs/images/landing.png),
[full answer](docs/images/desktop-answer-full.png),
[mobile](docs/images/mobile-answer.png) and
[local preview without an API key](docs/images/desktop-local-preview.png).*

## Quickstart

```sh
git clone https://github.com/Timerk/ResearchLens.git
cd ResearchLens
docker compose up --build
```

Open <http://127.0.0.1:4200> and ask, for example, *Why combine forward and backward
lighting for aircraft glass canopy inspection?* This starts the minimal tier, TF-IDF
retrieval, with no model downloads. Without an API key the app shows the ranked passages
selected by the same context budget as OpenAI mode, with full text and source metadata.
Generated answers need `OPENAI_API_KEY` in `.env`; see
[`.env.example`](.env.example). [docs/docker.md](docs/docker.md) covers the dense
tiers (`RETRIEVAL_TIER=auto` or `full`) and records a fresh-clone check.
[docs/development.md](docs/development.md) covers running without Docker.

## Try it

Open a recorded example to try the demo without using live-answer quota. For typed
questions without a visitor key, the server automatically selects live answers or
local preview.

| Request | What you get | OpenAI usage |
| --- | --- | --- |
| **Open a recorded example** | Replays a saved `gpt-6-luna` answer from the 2026-10-13 development evaluation with its cited passages. The label identifies the run, model and retrieval tier. | None |
| **Submit a question with live answers enabled and quota available** | Generates an answer with citations or reports insufficient evidence. The default limits are 5 per visitor and 50 in total per UTC day. Questions with no matching passages use no quota. | Owner's OpenAI key |
| **Submit a question in local mode (the default without a server key), with `DEMO_ONLY=true`, or after either quota is exhausted** | Shows the local preview with ranked passages and source metadata. Exhausted quota returns HTTP 429. | None |

If visitor keys are enabled, visitors can use their own OpenAI API key. The app sends
it in a request header for that request only. It bypasses the daily quotas, and the
input limits still apply. The server never stores, logs or returns the key.
Recorded answers come verbatim from the committed blind-grading
packet ([`owner-grading.md`](evaluation/reviews/2026-10-14-answer-judge/owner-grading.md));
[`researchlens_eval.demo_recordings`](backend/researchlens_eval/demo_recordings.py)
rebuilds [`data/demo/recorded-answers.json`](data/demo/recorded-answers.json) from it and
checks its hashes. Their passage text predates readable formulas, so one example shows
`[formula omitted]`.

## Architecture

```mermaid
flowchart TD
    subgraph ingest["Ingestion"]
        direction LR
        A["Article XML<br/>4 CC BY 4.0 papers"] --> B["MathML rendered<br/>as readable text"] --> C["207 passages<br/>with source locations"]
    end
    ingest --> D{"Retrieval tier<br/>chosen by free RAM"}
    D -->|"10 GiB"| E1["full<br/>Qwen3-4B"]
    D -->|"5 GiB"| E2["standard<br/>BGE-M3"]
    D -->|"2.5 GiB"| E3["light<br/>Qwen3-0.6B"]
    D -->|"0.25 GiB"| E4["minimal<br/>TF-IDF"]
    E1 & E2 & E3 & E4 --> answer
    subgraph answer["Answering"]
        direction LR
        F["Context budget<br/>12k or 16k characters"] --> G["Answer with citations<br/>or abstention"] --> H["FastAPI"] --> I["Angular frontend"]
    end
```

Ingestion turns the papers' XML into passages that keep section paths and paragraph
locations. At startup, auto mode loads the largest tier that fits in available RAM and
falls back to the next one if loading fails. The backend fills a character budget with
the top-ranked passages and sends them to the answer provider. The provider is either
a free local preview, which lists passages without an answer, or OpenAI. The backend
rejects any answer that cites an unknown passage or leaves a section uncited. Without a tier setting, the application default
is TF-IDF with four passages.

## Deployment and operations

The demo runs on one Hetzner Cloud CPX22 in Helsinki (2 vCPU, 4 GB RAM, about 20 EUR a
month including VAT and IPv4, billed hourly) with the same
Compose stack as local development plus
[`docker-compose.prod.yml`](docker-compose.prod.yml): Caddy terminates HTTPS and is the
only published service, nginx serves the app with security headers and proxies `/api`,
and the backend is never exposed directly. [docs/deployment.md](docs/deployment.md) is
the step-by-step guide: server, Docker, DNS, `.env`, light-tier indexing, start,
verification, monitoring and the tag-triggered GitHub Actions deploy.

- **Tier choice.** The server runs the light tier (Qwen3-0.6B, 2.5 GiB) because the full
  tier (Qwen3-4B) needs 10 GiB of RAM, which would cost several times more. `auto` falls
  back to minimal TF-IDF if light cannot load. Locally, `RETRIEVAL_TIER=auto` uses the
  full tier when the machine has the memory. The recorded answers were produced with the
  full tier and say so.
- **Limits.** Live answers: 5 per visitor (IP address, IPv6 /64) and 50 in total per UTC
  day, counted in SQLite on a volume so restarts do not reset them. Questions are capped
  at 2,000 characters and request bodies at 16 KB; OpenAI calls time out after
  45 seconds. Over a limit, or when OpenAI reports a rate or budget limit, the API returns
  HTTP 429 with the free preview. Optional Cloudflare Turnstile guards live answers.
- **Kill switch.** `DEMO_ONLY=true` disables every paid call, including visitor keys;
  recorded answers and previews keep working.
- **Budget cap.** A hard monthly budget (for example 5 USD) and a usage alert are set in
  the OpenAI dashboard, with a project key used only by the demo. At the 2026-10-13 rates
  the daily cap bounds spend at roughly 3 USD a month.
- **Monitoring.** A scheduled GitHub Actions workflow
  ([`uptime.yml`](.github/workflows/uptime.yml)) checks every 30 minutes that
  `/api/health` reports `"status":"ok"` on the light tier and that a recorded example
  loads; a failed run emails the repository owner.
- **Costs.** Server about 20 EUR a month (the cheaper CX23 was sold out); a free
  `sslip.io` hostname instead of a domain; OpenAI a few cents a day at most. The first
  live test answer used 3,696 input and 192 output tokens, about 0.0005 USD.
- **Limitations.** Visitors behind one shared address share a quota. The free endpoints
  have no per-visitor rate limit, only a concurrency cap. The online light tier retrieves
  differently from the full tier evaluated in [Results](#results-at-a-glance). Recorded
  examples show only the passages the answer cites.

A managed platform (Render, Fly.io, Railway) is a documented alternative, not a built
one: no server to maintain, but small instances fit only the minimal tier, free plans
sleep when idle, and without a persistent disk the quota resets on restart. See
[the trade-offs](docs/deployment.md#alternative-a-free-or-cheap-platform).

## Results at a glance

| Study | Result | Source |
| --- | --- | --- |
| Development retrieval | Qwen3-4B at 12k and 16k characters meets all five retrieval targets | [formula-adoption-results.md](docs/formula-adoption-results.md) |
| Held-out retrieval, pre-registered, run once | Qwen3-4B meets 4 of 5 strict targets. Recall@4 is 77.6%, below the 80% target. All five pass under the development whole-context convention | [held-out-results.md](docs/held-out-results.md) |
| Answer quality, development only | Complete required claims rise from 19/36 with TF-IDF and four passages to 32/36 with Qwen3-4B 16k and BGE-M3 16k | [answer-quality.md](docs/answer-quality.md) |
| Answer judge | Certified for required claims and abstention only. Application defaults unchanged | [answer-quality.md](docs/answer-quality.md#current-decision-2026-10-15) |

[docs/results.md](docs/results.md) walks through the whole sequence, from the original
problem to the answer-quality decision.

## How it was evaluated

- The project owner approved 86 evaluation questions, 50 for development and 36 held
  out, and separately approved the development evidence labels.
- The held-out set was frozen before model selection. Its protocol was committed
  before the first held-out search, and it ran once. The report includes the missed
  target.
- The owner and Codex independently graded 60 blind judge items. The judge was frozen
  before anyone opened the sealed validation half, and validation ran once.
- Decisions use paired, two-sided exact McNemar tests on the same questions. A
  pre-registered rule decided whether to change a default.
- Every paid evaluation run had an approved cost plan and a hard cap. All 449 calls in the latest answer
  study cost $0.2469 at the supplied rates, under a $3 cap.

## Tech stack

| Area | Tools |
| --- | --- |
| Backend | Python 3.13, FastAPI, scikit-learn TF-IDF, PyTorch, Transformers and ONNX Runtime on CPU |
| Models | Qwen3-Embedding 4B and 0.6B, BGE-M3, MiniLM, OpenAI Responses API with `gpt-6-luna` |
| Frontend | Angular 21, Vitest, Playwright |
| Tooling | uv, Ruff, pytest, Docker Compose, GitHub Actions |
| Hosting | Caddy (automatic HTTPS), nginx, SQLite for live-answer quotas |

## Project structure

```text
backend/researchlens/  API, ingestion, retrieval, answers
backend/researchlens_eval/  Offline evaluation toolkit and demo recording builder
backend/tests/         Offline pytest suite, no paid calls
frontend/              Angular app, Vitest and Playwright tests
data/technical/        Four CC BY 4.0 papers, extracted text, NOTICE
data/demo/             Recorded answers replayed by the public demo
deploy/                Caddyfile and deploy script for the VPS
evaluation/            Approved datasets, labels, reviews, cost plans
docs/                  Results and guides, start at docs/README.md
```

## Limitations

- The samples are small. With 36 answerable development questions and 26 held-out
  ones, the confidence intervals are wide.
- Most tuning used the development set. The held-out confirmation ran once and missed
  the recall@4 target.
- The answer judge is unreliable for qualifications, citation support and forbidden
  claims, so those results are diagnostics only.
- The full tier needs about 10 GiB of free RAM and an 8 GB model download. The minimal
  tier runs anywhere but retrieves less evidence.
- The corpus has four papers. Text extraction drops figures, tables and four
  unsupported formulas.

## License

The code and documentation are under the [MIT License](LICENSE). The four papers and
their extracted text keep their authors' copyright and CC BY 4.0 licenses. See
[data/technical/NOTICE.txt](data/technical/NOTICE.txt) for attribution and the changes
made during extraction.

## Development disclosure

The code, tests and documentation were written with AI assistance. The project owner
set the goals, constraints and budget, approved the 86 evaluation questions on
2026-10-01, and graded the judge validation items together with Codex. See the
[owner review](evaluation/reviews/2026-10-14-answer-judge/owner-review.md) for the
adjudication.
