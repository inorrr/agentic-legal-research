# Project Handoff Instructions

## Read first

Read README.md, docs/DECISIONS.md, docs/DEVELOPMENT_LOG.md, and PROJECT_TODO.md. Consult docs/ARCHITECTURE.md before changing module boundaries. User decisions in the current conversation override stale plans.

## Product context

Yinuo is building an individual course project for lawyers and has no legal background. The accepted goal is a working open-source, local-first case-research workspace, not a novel research algorithm. Keep the interface useful to lawyers and terminology understandable. Current implementation status must be stated honestly.

## Non-negotiable behavior

- Unlimited user-initiated Search again rounds with bounded agent work per round.
- Feedback is optional, revisable, and separate from saved cases.
- Relevance is not agreement with the user's position; retain relevant contrary cases.
- Never silently change explicit jurisdiction/court/date constraints.
- Ground explanations in identifiable source passages. Do not fabricate citations or treatment status.
- Separate global explicit preferences from matter-specific facts and feedback.
- No automatic cross-matter memory, model training, or multi-agent framework in the MVP.
- Local-first is not offline: explain cloud/source data flows accurately.
- No credentials, private matters, runtime databases, or unlicensed datasets in tracked files.

## Working conventions

Preserve faculty feedback files verbatim. Keep changes focused on the ordered checklist. Use meaningful tests for state, filters, adapters, and exports. Distinguish mocks/replays from real integration checks. Update README if implemented capabilities change, and append a dated entry to docs/DEVELOPMENT_LOG.md recording changes, checks, blockers, and the next action. Do not claim tests passed unless they ran.

Do not point the application at the course assignment remote in feedback_abel.md. Do not publish, send messages, or submit coursework without authorization. License selection remains pending; do not claim the project is already MIT-licensed.

## Latest handoff pointers

Product scope is general U.S. case discovery through CourtListener with explicit user filters. The agreed demo/evaluation topic is Fourth Amendment warrantless vehicle/container searches. The original six Supreme Court PDFs are fixtures and a local demo, not the permanent product scope.

Both OpenAI and CourtListener credentials are configured in ignored, owner-only `.env.local`; setup and reuse were authorized. Never print credentials, request them in chat, or recreate them. GPT-4.1 mini is configured. Current source integration passed three public-scenario rounds, including one model-assisted feedback round, exact excerpt checks, CSV, idempotency, and HTTP-server restart persistence. Reports are under data/live-source-checks; see docs/VALIDATION.md. Do not confuse the earlier anonymous401/DNS failures with current access.

The interrupted missing-text-cache fixes are complete; 157 backend tests, 7 frontend tests, and production build pass. Missing-text cache lasts 24 hours; positive opinion snapshots persist without update checking; matter deletion leaves the shared source cache. Four uncached CourtListener requests per round, conservative persistent limits of 5/minute, 50/hour, and 125/day, and provider 429 handling apply. Unlimited user-started rounds does not imply unlimited source requests.

The user confirms they have a reviewer. Do not report reviewer availability as unresolved or ask them to recruit another. The reviewer's relevant expertise, walkthrough, and findings have not yet been recorded. Remaining faculty feedback is tracked as future work in PROJECT_TODO.md: existing-tool comparison, reviewer guide/walkthrough, human effort, independent assessment, and actual contrary-case discovery. Retain the planned five-versus-about-twenty candidate-metadata experiment with bounded opinion reads. These are demo next steps, not completed validation or new recording prerequisites; browser rehearsal and delivery remain open.

Next: restart the user-owned launcher to load the new backend, create a new CourtListener matter (old demo matters preserve their scope), complete browser review and additional live questions, then record. Browser automation remains unverified because earlier launch was blocked. Official course details, license/remote, fresh checkout of current revision, professional review, and video/submission remain open. Do not claim submission readiness or redo already-passed paid checks without a new reason.

Recording fix (2026-11-14): the main workspace's latest failed round spent all four source requests on metadata searches without reading an opinion. Agent guards now prioritize reads and finalize at the request ceiling; optional pagination reserves opinion capacity, and cached reads remain usable. All 168 backend tests pass with synthetic/offline verification; no new live success is claimed. The current server on 5175 uses the main workspace and needs a restart to load this fix. The separate data/recording-session workspace remains unused. Preserve existing histories and the shared source quota ledger; see the latest development-log entry for the exact checks and next action.
