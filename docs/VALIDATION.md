# Validation Record — 2026-11-13

## Verified

| Check | Evidence / outcome |
|---|---|
| Official PDF import | Direct local downloads from GovInfo/LOC: 6 opinions, 175 pages, 378,221 extracted characters. Originals, hashes, and page text retained under ignored data/corpus. |
| Backend suite | 157 tests passed in the latest full run, including source caching/limits, missing text, provider errors, separate consent, fixed filters, evidence references, and workspace state. Model/source unit tests use simulated responses; separate live checks are recorded below. |
| Frontend | 3 transport tests and 4 source/consent/locator tests passed. TypeScript check and Vite production build passed. |
| Real local HTTP workflow | Three original synthetic matters searched actual imported text; source excerpts matched stored page substrings; feedback changed next query; independent selections exported with correct identities; history/settings/selections survived API restart. |
| Isolated installation | Fresh source copy in a temporary directory; new Python venv installed from exact-version requirements; npm ci; 60 backend tests and frontend build passed. This is not a Git checkout and not a cross-platform test. |
| Dependency caveat | Existing Starlette TestClient/HTTPX deprecation warning remains; tests pass. Python lock is a version snapshot without hashes, resolved on macOS arm64/Python 3.14. |

Real HTTP smoke output: `data/local-workspace-smoke.json` (ignored). Reproduce with `.venv/bin/python scripts/smoke_local_workspace.py`. The script uses a disposable database and disables model access; no private user data is touched.

## Observed real-source examples

For the full synthetic questions and facts (not just abbreviated keywords):

- Arrested driver: Ross, Acevedo, Gant in first round.
- Passenger purse: Houghton, Acevedo, Ross in first round.
- Covered motorcycle: Collins, Ross, Acevedo in first round.

Each next round displayed three previously unseen lexical matches from the six-case collection. This does not establish that the new cases were legally relevant or that feedback improved quality. Broad factual questions can prioritize general cases; the arrested-driver result illustrates why keyword rank should not be presented as legal relevance. Short keyword probes can produce different orders.

## Not yet verified

- **Browser UI:** Playwright workflow exists, but Chromium could not launch due to macOS sandbox Mach-port permissions. No screenshot, visual validation, or completed browser test is claimed. Its backend/Vite servers did start successfully. Run it outside this execution restriction or manually follow MIDTERM_WALKTHROUGH.md.
- **Broader evaluation:** Live CourtListener search and a model-assisted feedback round passed on one synthetic passenger-belongings question. Additional live questions and quality assessment remain open; new results alone do not establish improved legal relevance.
- **CourtListener pagination/coverage:** Authentication, actual limits, first-page search, and substantive opinion retrieval are verified. Pagination behavior has offline tests; live traversal beyond the first response, source updates, and collection completeness remain unverified.
- **Legal quality:** the user confirms a reviewer is available, but relevant expertise, the walkthrough, and findings have not yet been recorded. Exact quotation matching does not establish that the passage supports a legal interpretation, accurately attributes an opinion, or states current law. A reviewer guide, human-effort measurements, independent final assessment, and contrary-case discovery checks are planned in [PROJECT_TODO.md](../PROJECT_TODO.md#next-steps-from-faculty-feedback).
- **Delivery:** license, Git remote/commit, video, course requirements, and submission still pending.

## Reproduction

Use README install/import/start commands. Run backend tests and the local HTTP smoke script. For UI testing, install Playwright Chromium and run `npm run test:e2e` in frontend; ports 8000/5173 must be free. Browser tests use disposable state and always disable cloud calls. Review model outputs manually against sources before recording the agent demo.

## Connection-recovery follow-up

After a user reported Failed to fetch, both dev servers were confirmed stopped. Added a single-server launcher; verified actual UI HTTP response and the purse search on the same origin. Backend suite now 61 passing tests; three frontend transport tests pass (lost response, safe session refresh, retry limit). Static file boundary tests prevent serving configuration/data outside frontend/dist. The browser itself has not been visually verified.

## Successful live model checks — 2026-11-13

The confirmed project key was created through the encrypted setup flow, saved only to `.env.local` with owner-only permissions, and used successfully to list accessible models. Configured `gpt-4.1-mini`.

Two initial bounded attempts exposed strict quote-transcription failures and excessive duplicated source text. Changed final output to validated evidence IDs and compacted tool payloads without raising budgets. Successful direct run: 5 model calls, 4 tools, 12,490 input tokens, 524 output tokens, 26.8 seconds, three cases (Houghton/Acevedo/Ross). Original page offsets were independently checked for every returned excerpt.

A separate foreground single-origin HTTP run also passed: 5 model calls, 4 tools, 12,372 input tokens, 498 output tokens, 18.6 seconds, three cases. It used a temporary workspace and the real local configuration. Paid API usage occurred; no monetary estimate is claimed without a configured pricing basis. Reports remain ignored under data/live-checks/ and data/live-agent-foreground-http.json.

The detached background server on port 5174 could not reach OpenAI, while direct and foreground child execution succeeded. This is a launch-environment limitation, not evidence of an invalid key. The environment also denied stopping the earlier server and could not open Terminal. For continued use, start the provided launcher in the user's own terminal. It chooses a free port. No end-user browser test is claimed.

At that checkpoint, the backend suite passed 81 tests, including 27 agent tests. The launcher rebuilt the frontend successfully. The earlier clean-install result above predates later source integration and has not been repeated for the current revision.

## CourtListener setup helper

The hidden-prompt configuration helper passed **21 focused tests** using temporary configuration files and mocked access checks. These cover preservation of existing OpenAI settings, token validation, owner-only permissions, atomic replacement cleanup, symlink/nonregular rejection, cancellation, and credential-safe failures. These tests are included in the current full suite. The user subsequently entered the token locally; the authenticated probe passed. Its first retrieved record contained only 31 text characters, so that probe established access, not useful legal reasoning.

## Broader CourtListener integration — 2026-11-13

The account-usage endpoint returned limits of 5 requests/minute, 50/hour, and 125/day. Application tests use a dedicated public-scenario workspace under `data/live-source-checks`, sharing the source cache with the app. They do not modify private matters. The synthetic question concerns searching passenger belongings under the automobile exception, with all available U.S. courts and 1900 through the test date selected.

| Live check | Observed outcome |
|---|---|
| First source-search round | Query `"automobile exception" AND passenger` reported 2,851 matches; read three opinions outside the six-case demo (Lewis, Mitchell, Wilson). Four source requests, 8,886 ms; no model calls. |
| Feedback plus model-assisted second round | Current feedback requested focus on passenger belongings and the distinction between arrest and probable cause. The actual query included `passenger belongings`. Returned three new source identities (Nix, Hall, Lynn). Five model calls, four tools, four source requests, 20,942 input / 517 output tokens, 25,185 ms. All nine returned excerpts independently matched canonical text offsets, opinion/cluster identities, and hashes. CSV and repeated-request idempotency passed. |
| Third source-search round through a real local HTTP server | Reused the first query and its cached search page, retrieved three further source identities (Green, Mort, Lewis), three source requests, one cache hit, 6,664 ms; no model calls. All six excerpts matched stored text and hashes. CSV identities matched selections. UI HTML served on the same origin. After restarting the server, all three rounds, feedback, and selections were unchanged. |

The first two checks exercised FastAPI routes in-process while calling the real external APIs. The third used a foreground local server and actual HTTP requests. Neither method establishes browser rendering or completed user interaction. The two Lewis entries have different CourtListener case IDs; case-name text alone is not the deduplication key.

Reports are ignored local artifacts: `data/live-source-checks/first-source-round.json`, `model-feedback-round.json`, and `third-source-http-round.json`. The model check incurred API usage; no monetary estimate is claimed without a verified pricing basis. A changed query and new cases demonstrate functioning iteration, not a causal improvement in legal relevance.

After recovering the workspace connection, completed the missing-text cache safeguards and final verification: **157 backend tests, 7 frontend tests, and production build passed**. Known missing text is cached for 24 hours, unavailable candidates are deprioritized, cached opinion identities are rechecked, pagination limits remain visible, and long questions reserve space for positive feedback terms. No further paid model check was needed after the earlier live success. Existing dependency deprecation warning remains.
