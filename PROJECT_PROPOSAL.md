# Project Proposal: A Local-First Legal Case Research Workspace

## Goal and audience

Build a usable local case-research product for lawyers. A user enters a fact pattern and legal question, inspects cases and supporting passages, refines searches through optional feedback, and assembles an exportable collection. The goal is reliable end-to-end software, not a novel algorithm or a formal comparative research contribution.

The intended distribution is source code and setup instructions on GitHub or another code host. Users run their own instance and supply their own model access. The software should have no subscription fee; external model and source costs remain the user's responsibility. A license must be selected before an open-source release. Open source and local execution are product choices, not claims of uniqueness.

## First release scope

Support one local user, U.S. case discovery through CourtListener with explicit court/date filters, and one model provider. The product can search different legal topics within the available source collection; it does not require downloading the entire database. Retrieve promising opinions on demand and cache attributable text locally. Provider limits and collection coverage still constrain research; do not claim all U.S. law is covered.

**Demo and evaluation topic:** Fourth Amendment warrantless vehicle and container searches—for example, a passenger's purse, a vehicle search after arrest, and a motorcycle near a home. The six original Supreme Court opinions from 1982–2018 remain a reproducible local fixture collection, within its 1980–2020 filter window. They are not the product's permanent database or topic restriction. Live demonstration matters can include additional courts and dates selected by the user.

**Current implementation:** Authenticated CourtListener search, on-demand opinion text, and a model-assisted feedback round have passed engineering checks. Source selection, court/date filters, separate source/model consent, saved cases, CSV export, and display settings are implemented. Separate target-court fields, broader research preferences, and richer export controls below are planned refinements; browser and professional legal validation remain open.

### Core workflow

1. Create a matter with a fact pattern, research question, optional research position, and explicit court/date constraints. The target court and courts being searched are separate fields.
2. Search real cases and inspect names, citations when present, courts, dates, source links, relevance explanations, and source passages. Distinguish quotations from generated interpretation. Missing full text means no full-text-based analysis.
3. Mark cases relevant or not relevant with an optional reason. Feedback can be changed or removed; the latest state guides subsequent rounds.
4. Search again without a product limit on the number of user-initiated rounds. Bound calls, documents, tokens, and time inside each round. Prefer unseen cases, retain history, and explain no-new-result or interrupted rounds.
5. Save cases separately from voting. Persist the selection and export all or selected rows as CSV.
6. Set theme, text size, result density, export defaults, and explicit research preferences. Preferences must be inspectable, editable, and removable.

A case can be relevant despite an unfavorable outcome. Never interpret a negative vote as permission to suppress contrary authority. Do not automatically label a case as binding or valid law. Subsequent treatment is explicitly 'not checked' unless a future implemented feature establishes otherwise.

## Agent responsibilities

One bounded orchestration loop formulates queries, searches, reads opinions, locates evidence, and produces structured explanations. Query refinement uses the original question, confirmed preferences, retrieved evidence, and current feedback. It must not silently change explicit filters. Case text is untrusted evidence, not instructions to the agent.

Expose concise action records (queries, documents read, feedback used, stop reasons), not private reasoning. An optional clarification question is an extension, not a dependency for the first release. If implemented, it is skippable and inferred preferences remain unconfirmed until accepted.

## Personalization and local-first behavior

Separate personal display settings, explicitly confirmed cross-matter preferences, and matter-specific facts/feedback. Persist these locally; no model fine-tuning is planned. A preference inferred in one matter must not silently become a global rule. Automatic memory suggestions and behavioral adaptation are deferred until explicit settings work.

Local-first does not mean offline or that no information leaves the device. Search queries go to the data provider; required prompts and excerpts go to the cloud model. The product must explain this before the first external request. Store credentials only through the backend, initially environment configuration and later an OS credential store. Never include them in browser storage, exports, prompts, logs, or source control.

Initial downloads use the browser save dialog. An arbitrary export-folder setting is deferred until a controlled backend file writer or desktop packaging exists. Users should be able to delete local matters and preferences; deleting local records does not promise deletion from external providers.

## Technology plan

Use React + TypeScript + Vite for the local browser interface, Python + FastAPI + Pydantic for the backend, and SQLite through Python's standard library for persistence. HTTPX handles CourtListener requests; the official OpenAI SDK powers the optional agent. Use a small custom single-agent loop. No vector database, cloud server, accounts, or training pipeline is required initially.

Develop on Python 3.12+ and Node 22.12+. Pin resolved dependencies in lockfiles before release. Keep source/model adapters separate from the workspace domain so another provider can be added without rewriting the UI. See [architecture](docs/ARCHITECTURE.md) and [development guide](docs/DEVELOPMENT.md).

## Acceptance criteria and practical evaluation

The central question is whether someone can install the tool and complete the intended research workflow reliably. A three-condition retrieval study is not required.

- Reproduce setup from a clean checkout using the reviewer's own required credentials.
- Complete two or three documented public/synthetic research scenarios on real case data.
- Verify displayed quotations against opinion text, then separately assess whether explanations are supported.
- Demonstrate that feedback affects actual later query inputs/actions while explicit filters stay fixed.
- Verify history, votes, preferences, and selections survive refresh and restart.
- Verify CSV identities and row counts match the selection; handle spreadsheet formula injection.
- Exercise source failure, missing text, duplicates, revised feedback, and rounds with no new results.
- Record round latency, calls, token usage, and estimated cost with the pricing basis stated.
- Conduct a short task walkthrough with the reviewer's role/relevant expertise documented, noting task completion, confusion, perceived usefulness, and misleading explanations. The user confirms a reviewer is available; the walkthrough and findings remain pending. Record reading, judgment, feedback, and correction time separately from system latency. Until the review is completed, report engineering validation only.

Use small, clearly described examples and an honest limitations report. A successful demo is not evidence of comprehensive legal accuracy.

## Milestones and risks

1. Validate real source access and choose a focused demonstration/evaluation topic; reviewer availability is now confirmed.
2. Build the first slice: search, source inspection, selection, export.
3. Add persistent matters, iterative agent actions, optional feedback, and history.
4. Add basic settings, explicit preferences, and local-data controls.
5. Test failures, complete reviewer walkthroughs, reproduce setup, and prepare the midpoint/final artifacts.

Data availability, unreliable evidence generation, installation friction, and excessive scope are the main risks. Mitigate with an early source-access spike, source-linked claims, clean-checkout testing, and a small feature set. A permitted cached corpus can be a disclosed fallback; do not present fixtures as live retrieval.

Deferred: sophisticated clarification, automatic behavioral memory, local model support, desktop installers, advanced filters and authority classification, citation graphs, generated memos, rich annotation, collaboration, and non-U.S. sources.

**Potential extension — research monitoring:** explore an opt-in **Watch this research** feature for newly indexed matches and citations to saved cases. CourtListener email alerts could be the first version; in-app webhook delivery would require a separate reachable HTTPS receiver, reliable handling while the local app is offline, and confirmation of provider limits/costs. Any agent analysis remains optional and bounded. Monitoring dates must be explicitly chosen, and citation alerts do not establish legal treatment. This is future work outside the midpoint scope. See the [monitoring next step](PROJECT_TODO.md#potential-extension-research-monitoring).

## Faculty feedback and attribution

[Abel](feedback_abel.md) encouraged understanding existing tools, choosing a topic, and seeking meaningful relevance review. [John](feedback_John.md) flagged scope and access risks. Preserve their emphasis on evidence, contrary cases, and separate saving/voting while replacing the large comparative experiment with product validation.

**Planned follow-up:** document a concise comparison with existing tools; prepare a relevance-review guide; conduct the available reviewer's walkthrough and measure human effort; keep final judgments separate from search-steering feedback using unused questions and frozen outputs; and assess whether relevant contrary cases are actually discovered. Also test approximately twenty candidate metadata records per model search call against the current limit of five while preserving opinion-reading and source-request budgets. These are next steps for the midpoint presentation, not completed validation or a reinstated formal comparative study. See the [faculty-feedback checklist](PROJECT_TODO.md#next-steps-from-faculty-feedback).

External resources and AI assistance are listed in [ATTRIBUTION.md](ATTRIBUTION.md). Exact course deadlines, video limit, and submission format remain unconfirmed. See [the todo list](PROJECT_TODO.md) and [midpoint checklist](MIDTERM_DEMO_CHECKLIST.md).
