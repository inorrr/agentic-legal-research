# Agentic Legal Case Research

An open-source, local-first case-research workspace for lawyers: discover cases, inspect source evidence, refine searches through feedback, and save an exportable collection.

## Demo 1 — work in progress

[Watch Demo 1 on YouTube](https://youtu.be/doyNzaxG2VA).

**The product is still incomplete and under active development.** This first demo presents the current prototype; features, reliability, and evaluation are still being improved. It is not a finished legal-research product. See the [development checklist](PROJECT_TODO.md) for remaining work.

**Current status:** Working local workspace with live CourtListener case search, cached opinion text, optional bounded OpenAI research, persistent matters/rounds/feedback/selections, CSV export, and appearance settings. A real source search and model-assisted feedback round returned cases beyond the six-case PDF demo; exact source excerpts, export, and request idempotency passed checks. Court/date filters apply to the larger source. The six PDFs remain an independent local demo. This does not establish legal correctness. The browser UI builds successfully; browser execution remains unverified. See [validation](docs/VALIDATION.md).

**Product scope:** U.S. case search using the available CourtListener collection and user-selected filters. **Demo/test topic:** Fourth Amendment warrantless vehicle and container searches. This topic makes the midpoint examples consistent; it does not restrict the product to six cases or to that subject.

## Product workflow

1. Create a research matter with a fact pattern, question, and supported court/date filters.
2. Inspect real cases, relevance explanations, material differences, and linked opinion passages.
3. Optionally mark relevance and supply a reason; revise or remove feedback later.
4. Click **Search again** as many times as desired. Each round has a work budget, while prior results remain accessible.
5. Save cases independently of relevance votes and export the selection as CSV.
6. Configure appearance and explicit preferences stored locally. Automatic behavioral learning is deferred.

Relevant cases can challenge the user's position. Saving is not a relevance vote. Explicit filters must never change silently.

## Local-first and costs

The planned application stores research history, selections, and preferences on the user's device. Cloud model calls and database searches still send necessary information to external services. Free software does not mean free API usage. The initial integration will use a user-supplied OpenAI API key; do not assume a ChatGPT subscription provides unrestricted API access. Source access may also require credentials or payment.

## Run the local app

After the initial dependency setup below, configure CourtListener access for live search, or import the six PDFs for local demo mode. Double-click **Start-Casework.command** on macOS, or run from the project directory:

```bash
python3 scripts/start_local.py
```

This builds the frontend and serves both UI and API at http://127.0.0.1:5173 from one server. If 5173 is occupied, the launcher chooses the next free port through 5183 and prints/opens that URL. Keep the terminal open; Ctrl+C stops the app without deleting research. The macOS launcher opens the browser automatically. Use the URL printed by the launcher. An explicit port can be selected with `--port 5175`.

If the page says the local app is unreachable, restart the launcher and select **Retry connection**, or refresh the page. A browser tab can remain visible after its server has stopped. No API key is required for the local collection.

## Development quick start

Prerequisites: Python 3.12+ and Node.js 22.12+ with npm. Run from this directory. No credentials are needed for local corpus mode. Model mode requires separately configured OpenAI access and explicit in-app consent.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.lock
python -m pip install --no-deps -e ./backend
python scripts/import_demo_corpus.py
python -m uvicorn legal_research.main:app --host 127.0.0.1 --port 8000 --reload
```

For the two-process development mode, in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The frontend proxies `/api` to the local backend. Check http://127.0.0.1:8000/api/health directly if the status is unavailable. These commands start the local research workspace. The importer downloads six official PDFs from GovInfo/LOC into ignored local storage. Local searches make no model calls. The optional cloud checkbox remains unavailable until `OPENAI_API_KEY` and `OPENAI_MODEL` are configured. The single-server launcher reads these from the ignored project-root `.env.local`, with existing process-environment values taking precedence. Two-process development still reads the process environment unless Uvicorn is explicitly started with `--env-file .env.local`. It does not prove those credentials work until a live round succeeds.

Checks:

```bash
python -m pytest backend/tests
python scripts/smoke_local_workspace.py
cd frontend
npm run test:transport
npm run test:source
npm run build
```

Optional browser workflow test (requires permission to launch Chromium):

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

The test uses a disposable workspace, requires the imported corpus, and never calls OpenAI. It needs ports 8000 and 5173 free. If your environment cannot write the browser cache, set `PLAYWRIGHT_BROWSERS_PATH` to a writable directory for both install and test commands.

See [development instructions](docs/DEVELOPMENT.md) for configuration and module boundaries. Dependency lockfiles and actual validation results are tracked in [the development log](docs/DEVELOPMENT_LOG.md).

## Configure broader case-data access

After obtaining your own CourtListener API token, run this in a new Terminal window from the project root:

```bash
.venv/bin/python scripts/configure_courtlistener.py
```

Paste the token at the hidden prompt. The script preserves existing OpenAI settings, saves the new setting in owner-only `.env.local`, and checks a public search plus one opinion. It makes at most two CourtListener requests and no model calls. Only sanitized diagnostic metadata is reported. See [script instructions](scripts/README.md) for details.

Restart the app after configuration. Create a **new matter** with **CourtListener · broader U.S. case search**, select courts/dates, and accept the source-query disclosure. Enable the optional model and its separate disclosure for agent-assisted research. Existing local matters keep their original demo scope; they are not silently converted. Live search works without importing the six PDFs.

Each round permits up to four uncached CourtListener requests. After finding candidates, the agent prioritizes reading opinions before further searches; optional pagination reserves requests for those reads. A round can finish with fewer than three supported cases when its request allowance is used. Cached pages and opinions remain reusable. Search pages are cached for 24 hours; fetched opinion snapshots remain local for reuse. The app conservatively tracks 5 requests/minute, 50/hour, and 125/day; provider limits also apply. A stopped round displays its reason and any suggested wait. Missing opinion text is handled per case. Matter deletion does not clear the shared source cache. See [architecture](docs/ARCHITECTURE.md) for retention and source limitations.

## Documentation

- [Data source and initial topic](docs/DATA_SOURCE.md): Fourth Amendment vehicle searches, U.S. Supreme Court, 1980–2020; verified primary PDFs, access blockers, and reproduction steps.
- [Proposal](PROJECT_PROPOSAL.md): product scope and acceptance criteria.
- [Development checklist](PROJECT_TODO.md): ordered implementation steps.
- [Midpoint checklist](MIDTERM_DEMO_CHECKLIST.md): video and working-repo readiness.
- [Architecture](docs/ARCHITECTURE.md): stack, state, data flows, and boundaries.
- [Decisions](docs/DECISIONS.md): accepted choices and unresolved dependencies.
- [Agent handoff](AGENTS.md): rules for future development sessions.
- [Faculty feedback](feedback_abel.md) and [additional feedback](feedback_John.md): preserved original feedback.

## Search modes and limitations

- **Local collection:** deterministic keyword search over the six imported opinions. Positive feedback reasons expand the query, votes adjust order, and unseen matches are preferred. Negative reason text is retained but not interpreted. Keyword matches are not legal relevance judgments.
- **CourtListener search:** live case discovery with fixed court/date filters, pagination, unseen-case preference, and on-demand text retrieval. Without the model, optional search terms are used directly; otherwise a visible keyword query is built from the question and positive feedback. Source ranking is not a legal relevance judgment. Source-query sharing needs separate consent.
- **Optional model research:** available with either source. The model chooses search/read tools within fixed filters and round budgets, then selects delivered evidence IDs. The app copies exact excerpts from the stored source snapshot. CourtListener excerpts identify the opinion and application text section; PDF excerpts retain PDF pages. The UI requires consent to send the matter, feedback, and passages to OpenAI. Initial and feedback-driven live rounds passed; broader legal review remains pending.
- Source excerpts can include syllabi or separate opinions. Verify attribution and legal support in the linked PDF; exact text matching alone does not validate reasoning.
- Summary-length preferences affect model prompts; local keyword explanations do not change length. Automatic behavioral memory is not implemented.

Start the demo using the passenger-purse synthetic example. Follow [the walkthrough](docs/MIDTERM_WALKTHROUGH.md). See [what is needed from the owner](docs/OWNER_INPUTS.md) to close remaining submission blockers.

## Boundaries and attribution

Product scope: U.S. case discovery through CourtListener, one model provider, one local user. Demonstration questions concern vehicle/container searches; live search is not restricted to that topic. Specific court choices currently include the Supreme Court and federal circuits; **All available U.S. courts** also searches state courts. Records may include short procedural entries or separate opinions. No claim of exhaustive coverage, verified subsequent treatment, professional readiness, or algorithmic novelty. Desktop installers, local models, generated memos, collaboration, and automatic preference learning are later work.

This is an individual course project. The author remains responsible for understanding the system. See [ATTRIBUTION.md](ATTRIBUTION.md) for external resources and AI assistance. Source is available in the [public GitHub repository](https://github.com/inorrr/agentic-legal-research). An MIT license is proposed; license selection remains pending.
