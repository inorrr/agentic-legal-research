# Decision Record

## Accepted — 2026-11-13

- Deliver a working product; no requirement to establish algorithmic novelty or run a three-condition study.
- Local-first single-user browser workspace, open-source distribution intended, free software with external usage costs disclosed.
- React/TypeScript/Vite + Python/FastAPI + SQLite; one bounded agent and one provider initially.
- U.S. case search with explicit court/date filters. Keep a focused demonstration/evaluation topic; non-U.S. sources remain deferred.
- Unlimited Search again rounds, bounded work per round, optional editable feedback.
- Saved cases and relevance feedback remain independent; contrary cases can be relevant.
- Explicit settings and editable preferences first; automatic cross-matter learning deferred.
- Browser save dialog first; arbitrary download-directory settings deferred.
- Real quotes, source provenance, and honest coverage/treatment limits are core requirements.

## Open dependencies

- Broader coverage and live pagination checks. CourtListener authentication and actual limits are verified; public-distribution/product-access arrangements remain unresolved. See docs/DATA_SOURCE.md.
- Reviewer walkthrough and findings; the user confirms a reviewer is available. Record relevant expertise and completed assessment before claiming professional validation.
- Broader model evidence quality, feedback-driven repeat rounds, and cost evaluation. Initial model choice, credential integration, and live checks are complete as recorded below.
- License (MIT proposed), application remote, release/install packaging.
- Official midpoint/final deadlines, video duration, submission rules.

## Superseded

The earlier proposal centered on feedback/no-feedback retrieval experiments. That is no longer the core deliverable. Selective clarification and retrieval-disagreement policies are possible future features, not a claim of novelty or a prerequisite for implementation.

## Initial legal collection — 2026-11-13

Selected Fourth Amendment warrantless vehicle and container searches, U.S. Supreme Court only (`scotus`), decision dates 1980-01-01 through 2020-12-31. Begin with Ross, Acevedo, Knowles, Houghton, Gant, and Collins. This is a historical demonstration scope, not complete current law or a legally reviewed corpus. Three synthetic scenarios exercise material factual differences and retention of relevant contrary authorities.

Official U.S. Reports PDFs for all six seeds were readable through public web research. CourtListener's public index identifies Gant; its full opinion page was challenged, and the local API probe failed DNS resolution. No token is configured. Keep CourtListener as the intended search integration, but do not mark the live data-path gate complete. Official PDFs are a documented manual fallback, not an implemented import or search feature. No legally trained reviewer is secured.

## Midpoint implementation — 2026-11-13

Use the official-PDF local fallback now that direct downloads work; keep it visibly distinct from CourtListener search. The six cases are a demo dataset, not permanent product coverage. Implement optional OpenAI research without making live calls until new key setup is complete. User chose new-key creation; organization/project IDs and destination confirmation remain pending. Official submission requirements are not yet available.

## Live model integration — 2026-11-13

The user supplied organization/project IDs and confirmed creating and saving the new key to `.env.local`. Setup is complete; do not repeat creation or request those inputs again. GPT-4.1 mini passed direct and foreground HTTP public-scenario checks. Final responses select evidence IDs; the application copies verified source text instead of asking the model to transcribe quotations. Compact tool payloads and finalization after three read cases keep the original per-round budgets practical. This implementation decision does not establish legal correctness.

The launcher selects a free loopback port from 5173–5183 unless explicitly configured. Start it in the user's own terminal because detached execution in this tool environment could not reach OpenAI. Browser review and the live feedback/repeat demonstration remain next.

## Broader source and clarified topic — 2026-11-13

The user rejected six cases as sufficient product coverage. Implemented live CourtListener search with on-demand opinion reading and local caching. New matters choose source and scope; old local matters retain the original collection. All-courts search can retrieve state cases as well as federal cases. The product supports research across U.S. legal topics within available source coverage.

Keep **Fourth Amendment warrantless vehicle and container searches** as the midpoint demonstration/evaluation topic. The purse, arrested-driver, and motorcycle examples provide repeatable questions; they are not product restrictions. The six original Supreme Court PDFs remain fixtures and a local fallback. This supersedes earlier first-release wording that confined the entire product to one topic and six cases.

CourtListener credentials and account limits are verified. Three live rounds, including a model-assisted feedback round, returned additional case identities. Exact text, export, idempotency, and server-restart persistence passed. Browser demonstration and professional assessment remain pending. Source quotas, incomplete opinions, and unverified subsequent treatment remain explicit limitations.
