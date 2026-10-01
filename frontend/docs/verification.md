# Frontend verification — 2026-10-01

This work starts from `origin/main` at `3b7048c` on a separate
`frontend-verification` branch/worktree. It does not incorporate PR #8 or PR #9.
Backend APIs, retrieval, evaluation data, corpus files and model configuration are unchanged.
The fixture text in `testing/fixtures.ts` is explicitly mocked presentation data,
with the current `Answer`/`SearchHit` fields from `backend/researchlens/models.py`.
It is not scientific evidence or an evaluation dataset.

## Automated checks

Run these commands from `frontend` (Node 24 is the CI/recommended runtime):

```sh
rtk npm ci
rtk npm run check
rtk npm test
rtk npm run build
rtk npm run test:smoke:install
rtk npm run test:smoke
```

If RTK is unavailable, remove the `rtk` prefix. Linux CI installs browser system
dependencies with `npx playwright install --with-deps chromium` instead of the
browser-only installation command. Smoke tests own port 4300; stop other servers
on that port first. Dependencies and the browser need an initial download;
test execution needs no API key, backend server or paid API call.

| Check | Verified locally |
| --- | --- |
| Angular's `@angular/build:unit-test` / Vitest + jsdom | 21 component tests passed |
| Playwright / Chromium | 3 smoke tests passed |
| `npm run check` | Smoke/fixture TypeScript and formatting passed |
| `npm run build` | Production build passed, within Angular budgets |
| Existing backend checks, from repository root | `uv run pytest -q`: 33 passed; `uv run ruff check backend` and `uv run ruff format --check backend` passed |

Local runs used Windows, Node 22.22.0 and Python 3.13.14. The initial dependency
addition hit an npm 10 resolver error; using the repository-declared npm 11.17.0
resolved it. A subsequent clean `npm ci` succeeded. Backend tests emit an existing
Starlette TestClient/httpx deprecation warning. GitHub Actions uses Node 24 and
uploads browser reports and screenshots as `frontend-browser-results` for seven days.

Component tests exercise empty/whitespace/short/oversize questions, trimming and
the 2,000-character boundary, POST payloads, loading and duplicate prevention,
clearing stale answers/errors, health failure/recovery, successful answers,
section-to-citation association, source/license links and attribution,
technical and synthetic passages, plain-text rendering, local preview, no matches,
insufficient evidence, HTTP 429/503/504 errors, structured 422 detail, network
failure and retry. Native disclosure expansion is checked in Chromium rather
than relying on jsdom to emulate it.

Chromium smoke tests check Tab order through brand, question, submit, citation,
reference, license and source; Enter/Space submission and disclosure expansion;
focus retention during loading/retry; computed focus outlines; accessible
question naming; concise live status text and alert recovery; correct source
link attributes; and 320px preview, no-matches and answered layouts. Long XML
metadata is exercised with an explicit no-horizontal-overflow assertion.

## T3 collaborative browser inspection

The running Angular UI was opened at `http://localhost:4300` using the offline
mock server (`npm run start:mock`). Actual T3 keyboard interactions traversed the
brand, question and submit controls, submitted with Enter, retained button focus
during loading/completion, and expanded both citation/reference disclosures
using Enter/Space. DOM inspection confirmed the question label and descriptions,
read-only loading input, `aria-disabled` button, `aria-busy` result region, loading
and completion status text, source/license URLs and `noopener noreferrer` links.
At 320×740, T3 input interaction confirmed whitespace-aware validation,
`aria-invalid`, the disabled submit button and no initial horizontal overflow.

Full visual inspection **in T3** was blocked. `preview_snapshot` repeatedly returned
`PreviewAutomationExecutionError` with “Preview automation snapshot failed on client
preview-4adae1015e4c06e49eb804f6379bf250,” including after reopening/resizing and
opening another tab. The tool reported `visible: false`; `document.hasFocus()`
was false, so T3 could not verify rendered focus rings. During mobile submission,
the host disconnected and returned “No preview automation host is available” for
environment `41b52f2c-0c97-49a0-bba1-d74c7cd8c208`, with an instruction not to retry.
T3 mobile result inspection and T3 screenshot capture therefore remain incomplete.
The focus-ring and mobile-result evidence above comes from Chromium smoke tests.

## Captured visual evidence

Playwright captured desktop initial, loading, expanded answer, API error and
insufficient-evidence states, plus mobile expanded preview, no matches and
expanded answer. Those PNGs were opened and visually inspected locally; the
existing palette/layout remains intact and the source metadata wraps at 320px.
These are captured browser screenshots, not generated mockups or T3 snapshots.
Two representative screenshots are retained here; all states are produced under
`test-results/` and included in the CI artifact/HTML report. These are inspection
artifacts, not pixel-diff screenshot assertions.

![Desktop answer with expanded citation and reference](screenshots/desktop-answer.png)

![320px mobile answer with expanded citation and reference](screenshots/mobile-answer.png)

## Remaining limits

- No real provider calls, retrieval-quality assessment or factual-support evaluation
  was performed. Valid citation IDs only identify passages; people must assess support.
- Backend messages are displayed as returned. Current main's local preview/no-matches
  wording mentions lexical search; the frontend's own notice makes no assumption
  about future retrieval methods. Backend wording is outside this change.
- This checks Chromium CSS viewports, not Safari/Firefox, mobile device input,
  screen-reader announcements, or a full accessibility conformance audit.
- External source pages were not opened; tests check the link destinations and
  new-tab/security attributes without introducing external network dependencies.
- Full T3 screenshots, rendered focus visibility and mobile result inspection need
  a connected, visible preview host. Automated checks do not replace those checks.
