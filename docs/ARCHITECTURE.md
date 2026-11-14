# Architecture and Technology Decisions

## Stack

| Layer | Choice | Reason / status |
|---|---|---|
| UI | React, TypeScript, Vite; plain CSS | Small local browser app; workspace UI implemented; browser execution unverified |
| API | Python 3.12+, FastAPI, Pydantic | Typed contracts and Python retrieval ecosystem; workspace API implemented |
| State | SQLite via sqlite3; numbered SQL migrations | Single-user local persistence; implemented with schema version 1 |
| Source | CourtListener v4 through HTTPX, plus the local official-PDF demo | Live search, lazy opinion retrieval, and persistent cache implemented. Real source and feedback-driven model rounds passed through the application API. Browser walkthrough remains unverified. See DATA_SOURCE.md |
| Model | Official OpenAI Python SDK, model configured explicitly | Bounded Responses adapter; GPT-4.1 mini configured locally and live purse scenario verified |
| Agent | Small custom bounded tool loop | One bounded search/read orchestrator; no multi-agent framework |
| Tests | pytest + HTTPX; TypeScript build; later Vitest/Playwright | Add behavioral/browser checks when corresponding features exist |
| Distribution | Local source install first | Packaged desktop installer and Docker are deferred |

No vector database is required for the source-search approach. Avoid introducing training, orchestration services, or cloud hosting without a demonstrated need. The six official PDFs remain an offline test/demo source; they are no longer the only implemented source option.

## Current source integration status

The expanded application passed a real CourtListener keyword round and a subsequent model-assisted round using saved feedback. The first query reported 2,851 matches and retrieved three full opinion records. The next round returned three new cases in 25.2 seconds, using five model calls, four tools, four uncached source requests, 20,942 input tokens, and 517 output tokens. Nine returned excerpts were verified against the stored opinion text; export and request-idempotency checks also passed. These are API/engineering checks, not a completed browser walkthrough or professional legal validation. Reports are `data/live-source-checks/first-source-round.json` and `model-feedback-round.json`; see VALIDATION.md.

The product searches available U.S. case law with user-selected court/date filters. Fourth Amendment vehicle/container searches remain the demonstration topic, and the six official PDFs remain offline fixtures; neither limits the broader source's product scope. The earlier 20-result access probe and 31-character linked record established initial connectivity only. The account-usage endpoint reported the same 5/minute, 50/hour, and 125/day limits used by the app's conservative local limiter.

## Flow and boundaries

The browser talks only to the loopback backend, which owns secrets, SQLite access, source requests, and model requests. Vite proxies `/api` during development. The local launcher serves built assets and API from one loopback origin. Never expose the local API on all network interfaces by default.

Origin/host checks and a session token protect state-changing routes; localhost alone is not authentication. Keep explicit origins rather than wildcard CORS. Treat retrieved text as untrusted data. Do not give the model arbitrary filesystem or shell tools.

The orchestrator receives immutable explicit filters plus a snapshot of current feedback and confirmed preferences. It invokes typed search/read/passage tools within time, call, document, and token budgets. Record structured actions and stop reasons; preserve partial results on failure. The user starts every new round.

## Domain records and implementation notes

- Matter: ID, question, fact pattern, source, target court, search filters, timestamps. Existing matters default to the local source and retain their original filters.
- Case: source + stable case/cluster ID, metadata; opinion IDs and opinion type tracked separately so dissent/majority text is not mixed.
- Passage: opinion ID, source URL, exact quote, available locator, text-version hash.
- Round: matter ID, status, budgets, feedback/preference snapshot, queries, usage, stop reason.
- Result: round/case relationship, rank, explanation, linked passage IDs, seen/new marker.
- Feedback: matter/case ID, relevance, optional reason, revision timestamp; deletion removes its future influence.
- Selection: matter/case ID, optional user note, saved timestamp; independent of feedback.
- Settings: explicit display/export defaults. Preferences: confirmed scope, value, provenance, editable/deletable state.

Opinion snapshots and exact excerpts make old quotations inspectable. Source retention and redistribution must follow verified terms. Use transactions and schema versions; do not store secrets in SQLite. Runtime data belongs under ignored `data/` initially; a platform-specific user-data directory can follow packaging.

## Product invariants

- Unlimited user-started rounds; bounded work per round.
- Explicit filters remain fixed unless the user edits them.
- Latest feedback applies to future rounds; historic round snapshots remain auditable.
- Saving never votes; relevance is not favorable outcome.
- Deduplicate at case identity while retaining distinct opinion provenance.
- No invented quotes, locators, citations, or treatment status.
- Global preferences are explicit; matter facts never silently become global memory.
- Matter deletion removes matter state, not the separate shared source cache or remote provider retention. Cache deletion controls are not yet implemented.

## External interfaces and downloads

API credentials stay in backend environment configuration initially; OS keyring is a later usability improvement. Do not use `VITE_` variables for secrets. The single-server launcher loads allowlisted OpenAI and CourtListener settings from the ignored project-root `.env.local` into the backend process, without overriding existing environment variables. Direct Uvicorn execution uses process configuration unless an env file is explicitly supplied. The importer downloads official PDFs. Source queries require CourtListener consent; model analysis separately requires OpenAI consent. The earlier public live purse scenario passed against the local PDF source.

Cloud prompts and search queries leave the device; no 'fully offline' or 'nothing leaves your computer' claim. The local source cache stores query-bearing search URLs and public opinion text; matter deletion does not erase that cache. Avoid raw prompt logging by default and never log secrets. Export CSV through a download response and the browser save dialog; sanitize spreadsheet formulas. Arbitrary file paths, bulk opinion downloads, and configurable filesystem exports are deferred.

## CourtListener search and cache

`courtlistener.py` owns bounded HTTPS API access, fixed-filter verification, cluster/opinion identity checks, validated pagination, and `data/courtlistener-cache.sqlite3`. `source_search.py` provides optional keyword-only retrieval without model calls. The agent uses the same adapter for search and lazy reads; search candidates do not require fetching every full opinion. New CourtListener matters can search all available U.S. courts or filter to SCOTUS or a listed federal appellate circuit. The server accepts dates from 1600 through today; the UI defaults to 1900 through today. These are search filters, not a claim of complete source coverage. The old local source remains SCOTUS/1980–2020.

Each round permits at most four uncached source requests. A persistent local request ledger conservatively enforces 5/minute, 50/hour, and 125/day across rounds using the same cache. This ledger cannot account for requests made by another app or standalone probe; CourtListener's response remains authoritative. A 429 response records the required pause. Cached reads do not consume an API request. Unlimited user-started rounds remain supported, subject to per-round work and provider waiting periods. Pagination keeps filters fixed, prefers unseen cases, and reports when more results may remain.

Search-page responses are reusable for 24 hours, then fetched again when requested. A confirmed missing-text response is also cached for 24 hours so repeated rounds do not repeatedly spend requests on it; after expiry a later read may check again. Positive opinion snapshots persist indefinitely; update checking, opinion refresh, and cache eviction are not implemented. A newer search result does not prove the cached opinion text is current. Do not delete the cache merely to reset the local allowance, and do not promise that deleting a matter erases its cached query.

One lead/combined or otherwise available opinion is selected per case; other separate opinions are not automatically loaded. HTML is converted to a documented canonical text representation; plain text retains its text representation. Evidence consists of exact slices of that stored snapshot with opinion ID, hash, offsets, opinion scope, and source link. Text sections are local navigation units, not fabricated PDF/reporters' pages. Short records are labeled because a procedural entry may not contain substantive reasoning. Source retrieval and exact text matching do not establish legal relevance, complete opinion coverage, or subsequent-treatment status.

## References

- https://vite.dev/guide/
- https://fastapi.tiangolo.com/tutorial/first-steps/
- https://wiki.free.law/c/courtlistener/help/api/rest/v4/search
- https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety

## Current persistence and execution

SQLite schema version 1 stores matters, immutable round JSON snapshots, current feedback, independent selection snapshots, and settings. Transactions close connections explicitly. Mutations share a process lock where deletion/round state could race. Run a single backend worker; multi-process coordination is not implemented. Search request IDs provide idempotency for repeated requests carrying the same ID; the UI issues a new ID for each intentional round.

Local mode scans the imported six-case corpus, applies scope filters, prioritizes unseen matches, and returns up to three results. Positive reasons expand query text; negative reasons are not semantically interpreted. The optional model loop chooses search/read actions, validates model-selected evidence IDs against excerpts actually delivered by read_case and copies exact source text, and returns no unverified explanations on failure. Model limits: six calls, eight tools, 90-second round deadline, 2,000 output tokens per call, context-size guard. The observed-total-token threshold can be exceeded by one response; it is not a hard dollar cap. Usage is recorded; monetary cost is null until a verified pricing basis exists. Exact quote matching does not prove legal correctness.

Origin/host checks and a bootstrap-generated mutation token protect browser requests; no wildcard CORS. This is a loopback single-user app, not a hardened multi-user service. Never bind it publicly. Current preference scope is explicit display/summary settings; arbitrary preference memory remains deferred.

## Live integration hardening

The model references evidence IDs instead of transcribing source text. Registry entries retain page or opinion-text offsets, hashes, URLs, and opinion-scope labels; invented/unread/wrong-case IDs are rejected. Local PDF tools keep their existing page locators. CourtListener tools read exact text sections with opinion IDs and never convert those sections into PDF-page claims. Search tool payloads are compact, and reads deliver bounded excerpts. After reading three distinct cases, the next model request must finalize. The original six-call/eight-tool/90-second/observed-token limits are unchanged; the separate source-request budget also applies. SDK setup/provider failures produce sanitized failed/partial-round categories. HTTPX SOCKS support is installed for environments that supply a SOCKS proxy.

The launcher can choose an available port from 5173–5183. Host checks remain loopback-only; same-origin requests at the chosen loopback port are accepted alongside known development origins.
