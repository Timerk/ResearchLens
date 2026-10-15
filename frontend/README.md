# ResearchLens frontend

Angular 21.2 uses its built-in Vitest builder with jsdom for component tests.
Three Playwright/Chromium smoke tests cover native keyboard/disclosure behavior,
focus outlines, request recovery and narrow layouts that jsdom cannot verify.

Use Node 24 with npm (the repository declares npm 11.17.0). From this directory:

```sh
npm ci
npm run check
npm test
npm run build
npm run test:smoke:install
npm run test:smoke
```

The production build is written to `dist/frontend`. `npm run check` checks
smoke-test/fixture TypeScript and formatting of the changed UI and test files; Angular
compilation checks the application and component-test TypeScript during build/test.

`npm test` runs once and exits. Use `npm run test:watch` during development.
Component tests mock both `/api/health` and `/api/ask` using
`HttpTestingController`. Smoke tests intercept both endpoints in the browser and
start their own Angular dev server on port 4300. No backend, API keys or paid
provider calls are required. Stop another server using port 4300 before running
smoke tests. The first browser/dependency installation requires downloads.
On Linux CI, `npx playwright install --with-deps chromium` also installs OS dependencies.

The HTML browser report is in `playwright-report/`; screenshots for desktop/mobile
states and failure traces are in `test-results/`. Open the report with
`npx playwright show-report`. CI runs checks, component tests, the production
build and smoke tests, and retains browser artifacts for seven days.

For normal development with the local FastAPI backend on port 8000:

```sh
npm start
```

Open <http://127.0.0.1:4200>. See the [development guide](../docs/development.md) for
backend setup, or [Docker Compose](../docs/docker.md) to run both parts in containers.

For offline browser inspection of representative responses:

```sh
npm run start:mock
```

Open <http://127.0.0.1:4300>. This command runs Angular and a separate mock HTTP
server on port 4301. It never contacts FastAPI or an answer provider. The header
starts in the mocked OpenAI mode; mocked responses can update it. Question text
selects the response: `preview`, `no matches`, `insufficient`, or `error`;
anything else returns a mocked answer. Include `slow` for an eight-second delay
to inspect loading and duplicate prevention. Ctrl+C stops both servers.
Fixture claims are labeled as mocks and must not be treated as scientific findings.

Read the [verification record](docs/verification.md) for coverage, captured screenshots,
actual Chrome/T3 browser interactions and the precise browser-tooling limitations.
