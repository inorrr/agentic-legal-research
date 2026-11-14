# Owner Inputs and Remaining Gates

## Needed to finish the live-agent demo

**CourtListener setup and expanded API checks are complete locally.** No further token entry is needed. The first live application query reported 2,851 matches and retrieved three full case/opinion records. A model-assisted follow-up used saved feedback and returned three new cases; nine exact excerpts, CSV export, and repeated-request idempotency were checked. This validates the engineering workflow, not legal quality. The remaining demonstration gate is the browser walkthrough.

1. **OpenAI setup is complete locally:** the confirmed key was created securely and stored in ignored `.env.local`; GPT-4.1 mini was configured. Direct and foreground HTTP live purse checks passed. No further organization/project IDs are needed. Start the app in your own terminal using Start-Casework.command; this tool environment's detached server could not reach the API. The launcher now chooses a free local port automatically.
2. **Course requirements:** Official midpoint deadline/time zone, video duration/format, repository visibility/access, and submission channel. You indicated these are not yet available.
3. **Local browser verification:** Restart Start-Casework.command and use the URL it opens. Create a new matter with **CourtListener · broader U.S. case search**, select court/date filters, and review the separate source/model consent controls. Existing local matters intentionally remain on their six-case source. Record an actual search, evidence inspection, feedback/repeat, and export before claiming browser validation; this execution environment blocks automated Chromium launch. The vehicle/container example is a demonstration topic, not a restriction on the live source.

## Before publication/submission

- Initialize Git from a local terminal (`git init -b main`) if it remains uninitialized; environment writes to `.git` were blocked earlier. Specify the intended application repository/remote; do not use the course assignment URL by default.
- Choose an open-source license (MIT proposed). No license has been applied yet.
- Reviewer availability is confirmed by the user. Prepare the relevance guide and arrange the walkthrough with that reviewer as follow-up; record relevant expertise, findings, and human effort before claiming professional validation. No further recruitment is currently needed.
- Record the final video and submit the matching repository commit after live agent and UI checks.

## Source limits and local cache

CourtListener rounds are limited to four uncached source requests, with a persistent conservative allowance of 5/minute, 50/hour, and 125/day. The account's usage endpoint reported these limits; a provider rate-limit response still takes precedence because other tools may consume the same account allowance. Unlimited user-started rounds do not bypass these waiting periods.

Search pages and confirmed missing-text responses are cached for 24 hours. Positive opinion snapshots persist until explicitly removed; automatic opinion-update checks are not implemented. The cache contains search queries and public source text and is separate from matter history. Deleting a matter does not delete its source cache. Cache cleanup controls remain unfinished.

## Offline midpoint fallback

The six official PDFs remain useful for offline demonstrations and repeatable checks. They are a bounded test dataset, not the product's permanent case coverage. Broader U.S. source search is now configured and API-tested; keep its live workflow distinct from the offline fallback.
