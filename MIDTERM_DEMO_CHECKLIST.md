# Midpoint Video and Working Repository

The requested deliverables are a short video and a working repository. This is a proposed readiness checklist, not the official course rubric. Confirm deadlines, length, format, access, and whether local execution suffices.

## Current readiness (2026-11-13)

Live CourtListener discovery, a model-assisted feedback round, and a third source-search round passed on a public passenger-belongings scenario. Source excerpts, CSV, request idempotency, and restart persistence were checked; 157 backend and 7 frontend tests pass, and the production UI builds. Product scope is broader U.S. case search; the demo topic is Fourth Amendment vehicle/container searches. **Not submission-ready yet:** browser demonstration, video, and repository delivery remain open. The user confirms a reviewer is available; the walkthrough, legal-quality assessment, and broader evaluation remain planned follow-up, not completed validation. See [validation](docs/VALIDATION.md), [walkthrough](docs/MIDTERM_WALKTHROUGH.md), and [owner inputs](docs/OWNER_INPUTS.md).

Checked implementation items below reflect API/source tests, not a completed screen recording.

## Working slice

- [ ] Launch from documented instructions using a user's own required credentials.
- [x] Identify the actual supported topic, courts, dates, and source.
- [x] Enter a public/synthetic matter and retrieve real cases.
- [ ] Open a passage and explain how it supports one relevance explanation. Exact text matches and live source references are verified; browser evidence inspection remains pending. Professional interpretation review is planned follow-up.
- [ ] Give optional feedback, search again, and show its actual effect on agent actions. Live feedback snapshot, revised query, and new cases were verified through the API; the browser demonstration/recording remains pending.
- [x] Show retained history and filters; another round remains available.
- [x] Save cases independently of voting; export and inspect the CSV.
- [x] Refresh/restart and show persistent state if implemented.
- [x] Show basic settings or explicitly state they are unfinished.

A scaffold status screen alone does not meet the working-agent target. Label fixtures, cached data, replays, and edited waiting periods. Never claim subsequent-treatment verification or legal review that has not occurred.

## Repository readiness

- [x] Code, dependency locks, configuration example, and permitted demo scenario are included.
- [ ] Setup works from a clean checkout with stated runtime versions. Fresh source-copy install passed on macOS/Python 3.14/Node 22.20; no Git checkout or cross-platform validation yet.
- [x] Instructions distinguish user API costs from free software.
- [x] README lists implemented and unfinished capabilities accurately.
- [x] Credentials, private matters, and runtime databases are excluded.
- [x] Tests and a real integration-run record are available.
- [x] Architecture, data provenance, limitations, attribution, and license status are documented.
- [ ] Intended remote/access is verified; submitted commit matches the video.

## Suggested video outline

Use this approximately three-minute-and-twenty-five-second sequence only if the actual assignment allows it:

| Time | Content |
|---|---|
| 0:00–0:20 | Problem, lawyer audience, and local-first product |
| 0:20–1:00 | Research question, supported filters, real search |
| 1:00–1:40 | Case explanation and source passage |
| 1:40–2:25 | Feedback, Search again, action history |
| 2:25–2:50 | Saved cases, CSV, persistence/settings if ready |
| 2:50–3:25 | Implementation status, limitations, next steps |

Prioritize the working workflow over slides. No formal A/B/C study is required by this product plan. Explain actual outcomes, including no-new-result rounds.

## Next steps to explain in the recording

- [ ] Mention a documented comparison with existing tools and a short relevance-review guide as planned follow-up.
- [ ] State that a reviewer is available, with the walkthrough and findings still pending; include measuring human reading, judgment, feedback, and correction effort.
- [ ] Explain that final assessment will use reserved questions and frozen outputs, keeping evaluation judgments separate from search-steering feedback, and will assess actual discovery of relevant contrary cases.
- [ ] Mention the planned candidate-shortlist experiment: compare up to five versus approximately twenty candidate metadata records per model search call, retaining bounded opinion reads and provider requests. Assess relevance, new discoveries, human effort, response time, and model usage/cost.

These boxes track what the video explains, not completed experiments. See the speakable line in [the walkthrough](docs/MIDTERM_WALKTHROUGH.md#next-steps-to-mention-in-the-demo) and the [development tasks](PROJECT_TODO.md#next-steps-from-faculty-feedback). These follow-up tasks are not new midpoint recording prerequisites under the current product plan. Do not present improved relevance, completed legal review, or a larger implemented shortlist as established.

## Submission record

- Official deadline/time zone: TBD
- Video limit and format: TBD
- Video URL/file: TBD
- Repository URL and branch: TBD
- Demonstrated commit: TBD
- Verified setup/check commands: README installation, pytest (157 passed), frontend test:transport (3 passed), test:source (4 passed), npm run build; local PDF and live CourtListener integration records in docs/VALIDATION.md. Browser test remains blocked at launch in this environment.
- Actual source coverage: CourtListener U.S. case search within user filters; specific Supreme Court/federal circuit choices or all available U.S. courts, including state courts. Six official Supreme Court PDFs remain an independent local demo. Neither source establishes exhaustive/current law.
- Known missing verification/deliverables: browser workflow, additional live questions and pagination, professional review, fresh-checkout installation of the current revision, license/publication, recorded video.
- Submission channel/confirmation: TBD

See [PROJECT_TODO.md](PROJECT_TODO.md) for the full plan.
