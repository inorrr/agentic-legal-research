# Development Log

## 2026-11-13 — Product scope and repository scaffold

### Decisions and changes

Replaced the research-experiment framing in README, proposal, todo list, and midpoint checklist with a working local-first product plan. Kept faculty feedback files unchanged. Added architecture, development instructions, decision record, attribution, and root AGENTS.md for continuity.

Created React/TypeScript/Vite frontend and Python/FastAPI backend. The only API is GET /api/health; the frontend shows scaffold status and checks it through the Vite proxy. No model calls, real search, persistence, settings, memory, or exports are implemented. Added ignored runtime-data directory, placeholder environment configuration, Python manifest, exact-version Python dependency snapshot, npm manifest/lock, and backend smoke test.

### Checks performed

- Installed backend in project .venv on Python 3.14.0/macOS arm64.
- Installed frontend on Node 22.20.0/npm 10.9.3 using /tmp/legal-research-npm-cache after the default cache was unwritable.
- `python -m pytest backend/tests`: 1 passed. Dependency warning: Starlette TestClient deprecates its HTTPX integration; revisit the test transport on the next dependency update.
- `npm run build`: TypeScript check and Vite production build passed.
- Started both development servers and verified the frontend HTML and proxied /api/health over HTTP; stopped the processes afterward. No visual browser review performed.
- Python source/manifests parsed successfully; local Markdown links checked.
- npm reported zero vulnerabilities in the installed dependency tree at installation time. This is not a security audit.

The Python version snapshot is platform-specific and has no hashes; compatibility with the planned Python 3.12 minimum and other operating systems has not been tested. Clean-checkout reproduction remains outstanding.

### Blockers and remaining decisions

`git init -b main` failed because this environment does not permit creating `.git` in the project directory. Files were written successfully; no Git repository, commit, remote, or publication was created. The user can run that command locally. License remains unselected (MIT proposed).

Source access/terms, legal topic, court/date scope, legal reviewer, model choice, and official submission requirements remain unresolved. Do not confuse the course assignment URL in feedback_abel.md with the intended application remote.

### Next action

Validate CourtListener search and full-opinion retrieval on a small public example, document usable IDs/text/coverage/access terms in docs/DATA_SOURCE.md, then implement normalized case records and the first search → source inspection → selection → export slice. Follow PROJECT_TODO.md. No new product pivot or formal comparative study is needed.

## 2026-11-13 — Initial topic and real-source access investigation

### Decisions and changes

Selected Fourth Amendment warrantless vehicle/container searches, U.S. Supreme Court only, decision dates 1980-01-01 through 2020-12-31. Added docs/DATA_SOURCE.md documenting six primary sources, access observations, API field/identity expectations, current terms/limits/privacy, coverage boundaries, and the unresolved gate. Added six metadata-only seeds and three original synthetic scenarios under examples/vehicle_search/. Expected matches are engineering examples; no legal reviewer has been secured.

Added scripts/validate_courtlistener.py, a standalone standard-library probe separate from the application. It supports an environment token, hidden interactive token prompt, or explicit anonymous diagnostic; checks immutable scope and cluster/opinion links; rejects unsafe pagination and redirects; and saves only audit metadata and text hashes/lengths. Default budget is three requests; optional second page raises it to four. No credential persistence, model calls, retries, automatic quota management, PDF downloader, application source adapter, or corpus import was added.

Updated README, decisions, architecture source status, checklist, script/data instructions, and attribution. Faculty feedback files were not edited. No publishing, account changes, messages, or paid requests occurred.

### Checks performed and results

- Public web retrieval opened official full U.S. Reports PDFs for Ross (46 pages, Library of Congress), Acevedo (38), Knowles (7), Houghton (19), Gant (34), and Collins (31), the latter five from GovInfo. Inspected opinion text beyond syllabi and printed-page references. These are public web checks, not successful backend downloads or CourtListener API runs.
- CourtListener's volume 556 index exposed Gant's date, citation, docket, and cluster URL. Its opinion page returned a JavaScript/anti-bot screen. Browser fallback could not attach to its new tab; no browser verification is claimed.
- Reviewed current official CourtListener search/case-law/authentication/usage/terms documentation and GovInfo reuse policy. Defaults documented as 5/minute, 50/hour, 125/day; account-specific permissions and limits remain unverified.
- `.venv/bin/python scripts/validate_courtlistener.py --anonymous --output data/courtlistener-anonymous-check.json`: exited 1; one search request attempted, blocked by `dns_failure` before HTTP response.
- `.venv/bin/python scripts/validate_courtlistener.py --output data/courtlistener-auth-check.json`: exited 1; `token_missing`, zero requests. Checked only presence of the named environment variable and project `.env`; no secret was printed or written.
- `.venv/bin/python -m pytest backend/tests -q`: **24 passed** (23 synthetic probe tests and existing health test), in 0.27 seconds. Existing Starlette/HTTPX deprecation warning remains. These do not demonstrate live API access.
- Seed/scenario JSON parsed and cross-references, date windows, and page ranges checked. Frontend unchanged; no new frontend build or visual review needed for this task.

### Blockers and next action

The authenticated query → opinion-text gate is **not complete**. A personal CourtListener token and a runtime with working outbound DNS/network access are needed. Run the documented `--prompt-token` command from a terminal with source access, inspect the resulting real metadata/text fields, and exercise `--pages 2` if a next page exists within the account allowance. Do not mark credential, live pagination, API coverage, or text-path checks complete until observed.

After that, implement the normalized source adapter and first search → source inspection → selection → export slice. If access cannot be obtained, a manually curated official-PDF demonstration is possible but requires an importer and must be labeled accordingly. The six seeds alone are not exhaustive or current legal coverage. Git initialization, licensing, product-access arrangements before distribution, and legal review remain outstanding.

## 2026-11-13 — Midpoint implementation pass

### Built

Implemented the official-PDF importer and local lexical corpus, SQLite workspace/schema v1, typed matter/settings/feedback APIs, per-round snapshots, unseen-first retrieval, independent saved cases, sanitized CSV export, settings, and deletion. Added local host/origin and mutation-token checks, scoped feedback, explicit model consent, serialized mutations, explicit SQLite cleanup, and per-round request-ID idempotency.

Built the complete React workspace: scenario creation, fixed filters, case cards, source modal, positive/negative feedback and reason editing, round history/action traces, saved collection/export, settings, and responsive styles. Failed/partial model rounds display their status/stop reason rather than implying no relevant cases exist.

Added an optional OpenAI Responses tool loop with search/read tools, fixed filters, bounded calls/time/context, exact source-quote validation, sanitized errors, and usage records. Six model calls/eight tools/90 seconds maximum; observed total-token cutoff can be exceeded by one response. No live model requests were made. User selected new-key creation; secure picker unavailable, organization/project IDs not yet supplied, destination not confirmed. Do not create or write a key until the remaining setup inputs are resolved.

### Actual checks

- Direct official PDF import: six PDFs, 175 pages, 378,221 text characters. Source hashes/page provenance retained under ignored data/corpus.
- Backend suite: 60 passing tests, including 16 offline model-agent tests. Existing TestClient dependency deprecation warning remains.
- Real HTTP smoke across three synthetic matters: actual source passages, feedback-altered queries, repeated discovery, selected-case CSV, and backend-restart persistence passed. Report at data/local-workspace-smoke.json. No model calls.
- TypeScript/Vite build passed, including after frontend failure-state fixes.
- Isolated source-copy installation: new Python virtual environment from locked versions, npm ci, 60 backend tests, and frontend build passed on macOS arm64/Python 3.14/Node 22.20. Not a Git checkout or cross-platform test.
- Playwright workflow added and Chromium downloaded into /tmp/legal-research-browsers. Browser process cannot launch due to sandbox Mach-port permission denial; no visual screenshot, completed browser test, or video claimed. Tests remain available for local execution.
- Read-only review caught and fixed explicit SQLite connection closure and delete/write races.

### Documentation and next action

Updated README, development plan, midpoint checklist, architecture, data-source update, decisions, attribution, and AGENTS.md. Added OWNER_INPUTS.md, VALIDATION.md, and MIDTERM_WALKTHROUGH.md. Historical feedback files remain unchanged.

Next: obtain OpenAI organization/project IDs and confirm key destination through the credential flow, configure a supported model, run a real bounded agent scenario and inspect its evidence, then complete browser/manual verification and recording. Official course details remain unavailable. CourtListener token access, license, Git initialization/remote, legally trained review, video, and submission are still pending. The current six-case corpus is a demo dataset, not permanent product coverage. Do not call the project submission-ready or label lexical mode an LLM agent.

## 2026-11-13 — Failed-to-fetch recovery

User reported the purse example failed to fetch. Confirmed connection refused on both previous servers (5173/8000); browser had retained a page after those processes stopped. Added scripts/start_local.py and executable Start-Casework.command: build assets and serve UI/API together on 127.0.0.1:5173, with no auto-reload or separate proxy requirement. Only frontend/dist is exposed; private workspace/configuration paths remain outside the static root. Keep the user's local terminal open for a stable session.

Improved transport errors and Retry connection to preserve drafts/history, avoid replaying ambiguous failed writes, and refresh stale session tokens only after a known pre-handler rejection. Added three frontend transport tests and one static-serving/filesystem-boundary test. Backend: 61 passed. Frontend transport: 3 passed. TypeScript/Vite build passed. Real same-origin purse HTTP request completed with Houghton/Acevedo/Ross; temporary test matter removed. Browser visual verification still pending. Started a detached local launcher with logs in ignored data/local-server.log; it may still be subject to environment lifecycle, so the user-facing launcher remains the reliable local start path.

User has emailed for course requirements and awaits a response. User approved reasonable personal organization/project display names, but OpenAI assigns actual account IDs; none were supplied and no credentials were created. Proposed display names: Yinuo's Projects / Legal Research Agent. Credential setup remains separate from working local mode.

## 2026-11-13 — Credential destination preparation

User supplied the actual OpenAI organization and project identifiers in the conversation. New-key creation was previously selected; the proposed key name is Legal Research Agent. The secure picker/destination form remain unavailable. Verified the supported encrypted-key helper exists and the proposed root .env.local target is absent (not tracked; directory is not yet a Git repository). No key has been created or written. Final confirmation of the local destination is still required before creation.

Prepared local configuration so a securely saved key will be usable: the single-server launcher invokes legal_research.serve, which reads allowlisted .env.local settings inside the backend process. Explicit process values win, interpolation is disabled, symlink/nonregular targets rejected, and no secret values logged. Added python-dotenv and refreshed the dependency snapshot. Eight new configuration/server tests passed; full backend suite now 69 passed, with existing TestClient dependency warning. Tests used synthetic values only. Existing running server is not restarted until key/model configuration is ready.

After destination confirmation, use the official encrypted-key connector and helper with the user-supplied IDs; do not substitute another organization/project. Then configure a supported model and perform the bounded live test.

## 2026-11-13 — Confirmed key setup and successful live agent

The user confirmed the proposed key creation and destination. Created Legal Research Agent in the supplied Personal / Default project through the encrypted connector/helper flow. Saved the credential only to ignored `.env.local` with mode 0600, configured `gpt-4.1-mini`, and verified model access without exposing the key. Existing-key use for this project is authorized; do not recreate it. Added the missing HTTPX SOCKS dependency and refreshed the dependency snapshot.

Live testing exposed two implementation issues: model-transcribed quotations failed strict source matching, then duplicated page/snippet payloads exhausted the observed-token budget. Final responses now select validated evidence IDs; original source slices are copied into results. Search/read payloads are compact, pages remain bounded, and the agent finalizes after reading three distinct cases. Original round budgets remain unchanged. Provider failures are classified without exposing raw response bodies; client cleanup is guarded.

Successful direct public purse run: five model calls, four tools, 12,490 input / 524 output tokens, 26.8 seconds, three cases. Every excerpt was independently checked against stored page offsets. Successful foreground HTTP run: five calls, four tools, 12,372 input / 498 output tokens, 18.6 seconds, three cases, temporary workspace. Reports are ignored under data/live-checks/ and data/live-agent-foreground-http.json. These checks incurred API usage; no unsupported monetary estimate or legal-quality claim is made. Added opt-in scripts/validate_live_agent.py --live for reproduction.

All 81 backend tests passed, including 27 agent tests; the existing TestClient deprecation warning remains. The frontend production build passed during launcher startup. Earlier browser automation remains blocked; no visual test or recording was completed.

The launcher now accepts --port or chooses a free port in 5173–5183. The detached server on 5174 loaded the key but could not connect to OpenAI, while foreground execution succeeded. Stopping the old server was denied; opening Terminal from this environment was unavailable. The user must start Start-Casework.command in their own terminal and use its printed/opened URL. A synthetic demo matter in the persistent workspace contains the failed detached-server round; successful HTTP validation used disposable state.

Updated setup, architecture, attribution, validation, checklist, and handoff documentation. Next: verify the browser workflow using the local launcher, demonstrate optional feedback and a subsequent live model round, inspect interpretation against sources, then record the video. Course details, license/remote, publication and submission remain unresolved. Do not claim submission readiness.

## 2026-11-13 — Browser rehearsal handoff

User reports the app is open in their browser. Updated the recording walkthrough to reflect completed model setup, live initial checks, and the launcher's selected URL; corrected the submission-record test count. Browser-control tooling is unavailable in this session, so opening the page alone is not recorded as a successful end-to-end test. Next user check: cloud purse search, inspect evidence, save cases, give reasoned feedback, repeat search, export, and refresh to confirm persistence.

## 2026-11-13 — Broader case discovery takes priority

User stopped the demo sequence to flag the six-case database as too small. Audited the code: the limitation is real, with a fixed local corpus, SCOTUS/date validators, PDF-only evidence, and no paginated live search. Recommended live CourtListener search with lazy text retrieval/local cache; preserve the six cases as fixtures and existing workspace features.

Rechecked official provider documentation and local token presence without exposing credentials. No CourtListener token is configured. The bounded anonymous probe made one search request and received HTTP 401; it now reaches the API, so historical DNS failure is no longer the current observed blocker. No model calls or corpus downloads were made. Updated the ordered plan and source/handoff notes. Authenticated search/full-text validation is the next dependency; broader integration is planned, not implemented.

## 2026-11-13 — Private CourtListener token setup command

User obtained a CourtListener token and asked how to use it. Added scripts/configure_courtlistener.py for execution in their own interactive Terminal: hidden input, atomic owner-only .env.local update preserving existing settings, then the bounded public search/one-opinion probe (at most two source requests, no model calls). Empty/control/whitespace input and symlink/nonregular destinations are rejected; temporary secret files use an ignored .env.* name and are cleaned up. Errors never print raw provider exceptions. Failed access checks leave the entered token saved and report that access remains unverified.

Focused setup tests: **21 passed**, using only synthetic values in temporary directories and mocked network calls. Reviewed the helper and updated README, script instructions, owner inputs, and agent handoff. No real credentials were read or changed, and no live request was made in this implementation step. Wait for the user to run the command, then inspect data/courtlistener-auth-check.json and continue broader integration based on its actual result. Saving a token does not connect the app to CourtListener yet.

## 2026-11-13 — Live CourtListener integration and scope clarification

The user completed private token setup; authenticated search returned 20 records and text for one record. The first text was only 31 characters, so further checks used substantive opinions. Actual account limits were verified as 5/minute, 50/hour, and 125/day. Credentials remain local; no new credential setup is needed.

Implemented CourtListener source selection, user court/date filters, metadata-first search, bounded pagination with unseen-case preference, lazy opinion reading, and a shared SQLite source cache. Source requests and OpenAI analysis require separate browser consent. New live matters can search all available U.S. courts or selected Supreme Court/federal circuits; old local matters retain their fixed demo source. Source tools and the viewer distinguish opinion text sections from PDF pages, retain identities/hashes/offsets, and label short records and opinion types. One lead/combined or available opinion is read per case. No treatment checking or comprehensive opinion aggregation is claimed.

The first live query reported 2,851 matches and returned three cases beyond the six seeds in 8.9 seconds with four source requests. A second round with feedback and the live model used a revised query, returned three new source identities, and passed all nine exact-excerpt checks (five model calls, four tools/source requests, 20,942 input / 517 output tokens, 25.2 seconds). CSV and request-idempotency checks passed. These checks used actual external services through in-process API routes, not browser automation. Reports are under data/live-source-checks.

A workspace disconnection interrupted final review and documentation. After reconnection, completed cached identity checks and missing-text handling: a 24-hour negative cache avoids repeated unsuccessful fetches, unavailable records are deprioritized, other candidates remain searchable, and source-limit warnings survive cached reads. Positive feedback receives space even when a question is long. Positive opinion snapshots remain cached without update checking; deleting a matter does not delete shared source cache entries. Those limits are documented and reflected in the interface.

Final verification: **157 backend tests passed; 3 transport and 4 source UI tests passed; TypeScript/Vite build passed.** A third source-only round was exercised through a real temporary local HTTP server: three new source identities, three source requests and one search-cache hit, 6.7 seconds. Six excerpts matched canonical text/hash/opinion identity. Source-query filters and feedback snapshots were retained; CSV matched saved selections. Restarting the server preserved all three rounds, feedback, and selections. Same-origin UI HTML returned successfully; this does not establish rendered browser behavior. The temporary server was stopped. No further paid model check was necessary during recovery.

Clarified the product/demo distinction throughout proposal, README, decisions, plans, walkthrough, architecture/data-source notes, validation, and AGENTS.md. Product: general U.S. case discovery with source/user filters. Demonstration/evaluation topic: Fourth Amendment warrantless vehicle/container searches. Six original Supreme Court opinions: independent local fixtures, not a permanent database/topic restriction. Faculty feedback files remain unchanged.

Next user action: restart their local launcher and create a new CourtListener matter to load the updated backend/UI. Remaining work: browser demonstration, additional live questions and pagination, legal-quality review, fresh-checkout installation of this revision, official course details, license/remote, and video/submission. No publication or coursework submission occurred.

## 2026-11-13 — Candidate shortlist as demo future work

At the user's request, added a closing narration line and midpoint checklist item for testing approximately twenty candidate metadata records per model search call against the current five. Added the experiment to PROJECT_TODO.md with fixed questions/filters, bounded opinion reads and source requests, and relevance/discovery/time/usage measures. This is planned work, not a new implementation or a midpoint prerequisite; five is not a validated optimum. No runtime limits changed, live requests were made, or tests were rerun for this Markdown-only update. Next: mention the experiment during the demo's closing next steps and continue the existing browser rehearsal/recording checklist.

## 2026-11-13 — Faculty feedback follow-up and reviewer correction

The user asked to make remaining faculty-feedback items next steps, then clarified that they already have a reviewer. Updated current planning/status documents and AGENTS.md to reflect confirmed availability without claiming recorded qualifications or completed legal review. Historical log/decision entries retain their original status; this entry supersedes their earlier reviewer-availability statements. Fixture review-status metadata now says review is pending; expected cases and facts are unchanged.

Added explicit follow-up tasks for a dated existing-tool comparison, a short relevance guide, the reviewer's walkthrough, human reading/judgment/feedback/correction effort, final assessment kept separate from search-steering feedback, and actual discovery of relevant contrary cases. Retained the proposed five-versus-about-twenty candidate metadata comparison with existing opinion-reading/request budgets. Updated proposal, demo closing narration, and recording checklist; aligned both suggested timelines at approximately 3:25, subject to the unknown official limit. These are future work, not completed validation, new recording prerequisites, or a reinstated three-condition study.

No application behavior or runtime limits changed; no external requests, reviewer outreach, or publication occurred. Local documentation links and new section anchors passed checks; both fixture JSON files parsed with review-pending status. Reviewed status consistency and clarified that professional interpretation review is follow-up rather than a new browser-rehearsal prerequisite. No application tests were rerun for these documentation and descriptive-metadata edits. Next: continue browser rehearsal/recording and prepare the available reviewer's guide and walkthrough as follow-up.

## 2026-11-14 — Potential CourtListener research monitoring

At the user's request, added optional **Watch this research** monitoring to the development checklist, proposal, and demo notes. The potential feature would follow saved queries and citations, initially using native email alerts and possibly a separate HTTPS webhook receiver later. The plan covers endpoint protection, duplicate events, offline delivery, explicit monitoring dates, opt-in bounded model analysis, and provider access/cost checks. Citation alerts are not treatment verification, and webhooks do not automatically refresh cached opinion text. Included official provider references and an optional brief demo closing line.

This is planning only: no webhook endpoint, alert subscription, hosted service, or model call was created. No runtime behavior changed; application tests were not rerun for these Markdown-only edits. Existing browser rehearsal and reviewer follow-up remain the priority.

## 2026-11-14 — Recording workspace preparation

The user is preparing to record. Found older servers on 5173 and 5174 still exposing the six-case backend without CourtListener capability. Rebuilt the current frontend successfully and started an isolated recording workspace on 5175 using existing credentials and the main CourtListener cache/request ledger. Existing user matters were not modified or deleted. Runtime launch helpers and preparation reports are under ignored data/recording-session.

Health, current capability flags, and UI HTML passed local HTTP checks. A single bounded public-scenario preflight received a model response but failed at the CourtListener search tool: one model call, one tool/source attempt, 1,096 input and 26 output tokens, about 12.7 seconds, no cases returned. A separate network probe reported a CourtListener hostname-lookup failure; HTTP access to its root returned 403. This run does not supersede the earlier successful source checks with a claim of current connectivity. No browser-control connection was available; no visual verification is claimed.

Removed only the temporary preparation matter, retaining its diagnostic report, then created a clean passenger-purse matter with all-courts wording, 1900–2026-11-14 dates, zero rounds, no feedback, and no saved cases. Corrected the walkthrough's question/scope mismatch. Stopped the tool-owned recording server and verified port 5175 is free, the launcher is executable, and the persisted recording database contains one matter with zero rounds/feedback/selections. The user can launch data/recording-session/Start-Recording.command in their own Terminal on 5175. Confirm a successful live search there before recording; no further credential setup is needed. No application code changed, and the full test suite was not rerun.

## 2026-11-14 — Preserve opinion reads within the source budget

The user reported a recording round stopping at the four-request source budget. The latest round in the main workspace showed four successful metadata searches, each returning five candidates, followed by a budget failure with no opinion read. The running current server on 5175 uses the main workspace; the separate recording workspace still has zero rounds. Older servers on 5173/5174 remain stale. No user matters, rounds, feedback, selections, credentials, or source ledgers were changed.

The agent now requests an opinion read after discovery, blocks repeated metadata searches when capacity is needed for evidence, and completes with supported results when its uncached allowance is used. Known cached unread opinions remain eligible. The execution guard rechecks policy for every tool call, including unexpected multiple calls in one model response; provider failures and finalization cannot be bypassed by extra calls. Optional uncached pagination reserves capacity for up to three discovered opinions, with a distinct pagination-pause note rather than a false error. Actual provider limits and missing-text failures remain explicit. The four-request ceiling and persistent 5/minute, 50/hour, 125/day limits are unchanged.

Validation: **168 backend tests passed**, including a synthetic replay of repeated query variations, normal search-plus-three-read completion, fewer-result finalization, cached reads at zero remaining requests, empty-query refinement, sparse pagination, and same-response guard enforcement. Tests use synthetic model responses and mock HTTP sources; no live provider call or browser verification was performed for this fix. Frontend files were unchanged, so the earlier successful build was retained. Next: restart the user's launcher to load the backend changes, open its displayed URL (currently 5175), and start another round before recording. Existing failed rounds remain as honest history.

## 2026-11-14 — Demo 1 link and credential audit

Added the user's video link, https://youtu.be/doyNzaxG2VA, near the top of README and to the midpoint submission record. Labeled it **Demo 1 — work in progress**, explicitly stating that the product is still incomplete. The video itself was not reviewed, and adding its link does not establish completed checklist steps or course submission.

Credential audit found no configured OpenAI key or CourtListener token in 66 tracked/current working files, all 66 local Git blobs (including any unreachable objects), the one local commit object, or the three built frontend files. Exact raw-value and Base64 comparisons ran in memory without printing credentials. An independent token/private-key/credential-URL scan found only synthetic test values. The tracked .env.example contains blank credential fields; no runtime database is tracked. The real .env.local is untracked, ignored, and owner-only (0600). Backend/bootstrap/frontend configuration review found no provider-key exposure to the browser.

GitHub metadata confirms the repository is public. Its sole advertised branch/ref, main at af10428460cc920e0c619bf22215392d602494be, matches the scanned local commit. This audit covers repository files/history and the local frontend build, not video frames, external logs, or credentials in unrelated locations. No credentials were changed or revoked. Markdown/diff checks passed; no application tests were rerun for this documentation-only step. These documentation edits and the previous budget fix remain local and uncommitted; no push occurred. Next: commit and publish the intended changes, then record the demonstrated/submitted commit accurately.

## 2026-11-14 — Authorized publication handoff

The user requested a push of the pending changes: Demo 1 link and incomplete-product label, opinion-reading budget fix and regression tests, and associated planning/handoff updates. Final review found no publication blockers; the earlier 168-test backend result applies to the unchanged code. README now identifies the existing public repository and retains the pending-license limitation.

Local Git metadata is read-only in this session. Publication therefore uses GitHub's Git-data API with the existing main commit as parent and an expected-head check, without force-pushing or rewriting history. This leaves the local working files in place but does not advance local Git history. A future session must inspect the remote head and synchronize the checkout before creating another local commit; do not republish these same changes as an unrelated commit. This publication does not establish that the video demonstrates the exact submitted revision or that coursework has been submitted.
