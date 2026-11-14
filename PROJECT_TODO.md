# Development Checklist

Check items only after verifying them. This project prioritizes a working local product; a novel algorithm and formal three-condition study are not required.

## Current priority: validate and demonstrate broader discovery

Live CourtListener search is implemented and exercised beyond the six original cases. Product scope is U.S. case discovery with explicit filters; the demonstration/evaluation topic remains Fourth Amendment vehicle and container searches. The six PDFs are regression/demo fixtures.

- [x] Configure personal CourtListener API access and verify search → full opinion text. Authenticated source retrieval and a model-assisted feedback round passed.
- [x] Add live search with lazy full-opinion retrieval, pagination, stable identities, and a local evidence cache. Pagination behavior is tested offline; live checks have used the first page's candidates.
- [x] Make source selection and supported court/date filters explicit instead of hardcoding the demo collection.
- [x] Support source-specific evidence locators and opinion types; retain exact-text checks without inventing PDF page numbers for HTML text.
- [x] Apply provider request limits and disclose source-query sharing separately from model consent. Observed account limits match the conservative local defaults.
- [ ] Verify multiple distinct questions and at least three user-started rounds. Three rounds of the public passenger-belongings question returned new cases; additional live questions and browser demonstration remain pending.

Keep existing matter history, optional feedback, selections, and export. A larger imported public corpus remains a fallback if live access is unavailable; index larger local collections instead of rescanning every page per request.

## 0. Foundation

- [x] Rewrite product scope around local-first, user-supplied model access, and iterative case collection.
- [x] Choose the stack and document architecture and module responsibilities.
- [x] Create a backend/frontend development scaffold and agent handoff instructions.
- [ ] Resolve and lock dependencies; verify startup and build from a clean checkout.
- [ ] Choose a license (MIT proposed) and application repository name/remote before publication.
- [ ] Confirm midpoint/final deadlines, video length, and repository-access requirements.

## 1. Validate the data path — next priority

- [x] Test CourtListener credentials with real search and opinion retrieval; inspect actual account limits. Public-distribution/product-access terms remain a separate release gate.
- [ ] Extend coverage checks across more questions and live pagination. Case/opinion IDs, dates/courts, source links, exact text, and account limits were checked on live samples; pagination safeguards have offline tests.
- [x] Choose one legal topic, court subset, and date window; record coverage in docs/DATA_SOURCE.md. Vehicle/container searches; SCOTUS; 1980–2020; six official PDFs inspected through public web research.
- [x] Confirm reviewer availability. The user confirms they have a reviewer; the walkthrough and review findings remain pending.
- [x] Prepare two or three public/synthetic scenarios; add permitted fixtures and their provenance. Three original scenarios and six metadata-only seeds in examples/vehicle_search/.

Exit: a documented, reproducible path from a query to usable real opinion text.

**Initial source-access gate passed.** CourtListener now supplies real cases and opinion text to the application. Broader coverage, professional review, and live pagination beyond the first response remain to validate.

## Current implementation update

Live CourtListener search and optional model research are implemented. The official-PDF collection remains a separate fallback. See docs/VALIDATION.md for real versus simulated checks; browser validation is still pending.

## 2. Build the first vertical slice

- [x] Define Pydantic records and versioned SQLite schema/migrations.
- [x] Implement the official-PDF local corpus and CourtListener adapters, stable identities, filtering, and attributable text loading.
- [x] Add query entry, results, and a source viewer; label unavailable text/metadata.
- [x] Add the provider adapter and bounded single-agent loop with exact source checks. A live CourtListener feedback round passed; broader legal-quality review remains pending.
- [x] Keep secrets server-side; validate provider access without logging credentials. Confirmed key saved in ignored owner-only configuration; model listing and direct/HTTP research checks passed.
- [x] Implement separate save/remove selection and CSV export with formula-injection protection.
- [x] Complete one real question → source passage → saved case → export HTTP walkthrough (three scenarios). Browser demonstration pending.

## 3. Iteration and persistence

- [x] Persist matters, rounds, constraints, source references, votes/reasons, and selected cases.
- [x] Implement feedback revision/removal and snapshot the feedback used for each round.
- [x] Implement unlimited user-initiated Search again with bounded per-round work. Both modes implemented; initial model round live-verified.
- [x] Prefer new cases, deduplicate, retain earlier results, and report no-new-case rounds.
- [x] Show queries/actions and retain the feedback snapshot used by each round. A live follow-up used a revised query and returned new candidates; this does not prove improved legal relevance.
- [ ] Preserve explicit filters and relevant contrary cases; do not conflate saving with voting.
- [ ] Handle interrupted rounds, retries, partial results, and duplicate submissions. Request-ID idempotency and model failed/partial states implemented; process-kill recovery and full retry UX remain to test.

## 4. Settings and local control

- [x] Add theme, font size, density, and summary-length setting. CSV is the sole export format; browser controls download location.
- [ ] Add explicit global preferences separately from matter-specific context.
- [ ] Support inspect/edit/delete/reset for preferences and local matters.
- [ ] Explain external data flows before external requests; disable telemetry by default.
- [x] Provide browser-based downloads; do not promise an arbitrary export folder yet.
- [ ] Add optional keyring-backed credential setup if time permits.

## 5. Validation and midpoint

- [x] Test filters, feedback revisions, deduplication, persistence, selection independence, and CSV output.
- [x] Test missing text, source timeout/rate limit, model failure, and budget exhaustion using simulated failures. Missing-text checks are cached for 24 hours, and available candidates remain searchable.
- [ ] Audit quotations and explanation support separately, including contrary cases.
- [ ] Run a fresh installation and a real integration scenario; separate mocks/replay from live runs.
- [x] Record measured latency, calls, usage, and cost estimates where available. Two successful live checks recorded in docs/VALIDATION.md; monetary estimates omitted because pricing is not configured.
- [ ] Complete MIDTERM_DEMO_CHECKLIST.md; state unfinished work honestly.

## 6. Release preparation

- [ ] Complete reviewer walkthroughs and summarize findings/fixes in docs/VALIDATION.md.
- [ ] Add license, third-party attribution, dependency locks, and supported runtime instructions.
- [ ] Verify repository contains no credentials, private matters, or unlicensed datasets.
- [ ] Reconcile README and screenshots with implemented features.
- [ ] Publish only to the intended remote when authorized; record demonstrated commit and submission links.

## Next steps from faculty feedback

These are planned follow-up tasks to mention in the midpoint demo. They do not reinstate the three-condition study or add new recording prerequisites under the current product plan; official assignment requirements still need confirmation. Reviewer availability is confirmed, but no completed legal review is recorded.

- [ ] Document a brief comparison with existing tools, including Harvey, using dated official product sources. Compare case discovery, source inspection, feedback, saved collections, and local execution; distinguish documented capabilities from unknowns without claiming uniqueness.
- [ ] Prepare a short reviewer guide defining relevance through the legal issue, material facts, selected court/date scope, and supporting passages. Record favorable/unfavorable outcomes separately from relevance, and allow uncertain judgments with reasons. Verify explanation support separately from exact quotation matching.
- [ ] Run a walkthrough with the available reviewer. Record their role/relevant expertise, task completion, confusing interactions, usefulness, and misleading or unsupported explanations. Summarize findings and follow-up fixes in docs/VALIDATION.md; availability alone does not establish professional validation.
- [ ] Record human effort: time spent reading cases, judging relevance, entering feedback, and correcting explanations, separately from system waiting time, model usage, and API costs. Include that effort in any efficiency comparison.
- [ ] Keep final assessment independent of search-steering feedback. Reserve unused public/synthetic questions, freeze the outputs before assessment, and keep final evaluation judgments out of search inputs during the assessed run. Label reused demonstration questions as development examples rather than independent evidence of improvement.
- [ ] Assess actual discovery of relevant contrary cases with the reviewer. Identify a small set of relevant favorable and unfavorable examples, inspect retrieved and missed cases, and report limits. Eligibility safeguards and a small reviewed sample do not establish comprehensive legal recall.
- [ ] Test a larger candidate shortlist: compare the current limit of five metadata records per model search call with approximately twenty, using the same reserved questions and filters for both settings and the independent assessment above. Keep opinion-reading and source-request budgets bounded; assess relevance (including contrary cases), new relevant discoveries, human effort, latency, and model usage/cost where available. Document review results before choosing a new default. This remains future work, not a demonstrated improvement.

## Potential extension: research monitoring

- [ ] Explore an opt-in **Watch this research** feature after the core workflow and reviewer evaluation: notify lawyers when CourtListener indexes new results for a saved query or new material cites a saved case. This is a potential extension, not a midpoint requirement or implemented capability.

Start with CourtListener's native email alerts as a lower-infrastructure option. If in-app notifications prove useful, assess a separate reachable HTTPS webhook receiver and queue, endpoint protection, duplicate-event handling, and delivery when the local app reconnects. Keep the existing loopback app private. Users should be able to pause or delete watches; incoming results should link to the originating matter for review without automatically changing its filters or saved-case collection. Optional agent analysis should require consent and retain per-run usage budgets; receiving an alert alone should not trigger paid model calls.

Confirm provider access, alert limits, and any service/hosting costs before implementation. Monitoring needs an explicitly approved ongoing date window; never silently extend a matter's fixed cutoff. Search alerts use keyword queries. Citation notifications are leads for review, not verification of negative treatment or current law. Webhooks do not replace interactive search or guarantee that cached opinion snapshots are refreshed.

Provider references, consulted 2026-11-14: [Alert APIs](https://wiki.free.law/c/courtlistener/help/api/rest/v4/alerts), [webhook setup](https://wiki.free.law/c/courtlistener/help/api/webhooks/getting-started), and [webhook events and terms](https://wiki.free.law/c/courtlistener/help/api/webhooks/about).

## Later, only after the core works

Automatic memory suggestions; selective clarification; local models; desktop installers; configurable export folders; memos; advanced comparison; citation graphs; collaboration.
