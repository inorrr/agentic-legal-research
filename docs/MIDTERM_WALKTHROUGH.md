# Midpoint Walkthrough and Recording Plan

Status: rehearsal plan, not a recorded or submitted video. Official video length remains unknown. Live CourtListener search, a model-assisted feedback round, and three-round persistence/export checks passed through the API. Browser demonstration remains pending. Product scope is general U.S. case discovery; the repeatable demo topic is Fourth Amendment vehicle/container searches. Never describe keyword-only retrieval as an autonomous LLM agent.

## Prepare

1. Follow README setup, then start or restart Start-Casework.command and keep its terminal open. Existing local OpenAI/CourtListener setup is complete. Use public/synthetic facts only.
2. Use the URL opened or printed by the launcher; it selects a free port from 5173–5183. The source label should identify CourtListener for the broader demo. The six-case local collection remains a separate source option.
3. Click **＋ New matter**, choose the CourtListener source and **Probable cause and a passenger's purse** under **Start with a synthetic example**. Keep **All available U.S. courts** and the chosen dates visible. Replace the example's Supreme Court-specific question with **How do courts address searches of passenger-owned containers when police have probable cause to search a vehicle?**, then click **Create matter →**. Older local matters retain their original scope; create a new live matter rather than assuming they changed.
4. Accept the separate CourtListener query-sharing notice. For the agent rehearsal, enable **Use configured cloud model** and accept the OpenAI disclosure. These are separate data flows; model usage incurs API costs.
5. Optionally start with search terms `"automobile exception" AND passenger`. The model may refine the query; show its actual recorded actions. Provider limits still apply: wait when the app reports a pause. Do not edit a throttled round to look like uninterrupted retrieval.

## Walk through the product

1. Search CourtListener. Explain that the agent discovers candidates from a larger source, then reads promising opinions. Results may vary; the observed 2,851 matches belonged to one test query, not a permanent collection count or legal answer key.
2. Click **Inspect evidence ↗**. Show an exact excerpt, its opinion identity/text-section label, source link, and opinion scope. CourtListener text sections are application locators, not reporter page numbers. For the separate local PDF mode, show PDF pages and OCR limitations instead. Do not claim treatment checking.
3. Click **＋ Save case**. Show that this does not set relevance feedback.
4. After inspecting a case, click **Relevant** or **Not relevant**. Enter a case-specific reason in **Optional feedback reason** and explicitly click **Save reason**. A research priority used in testing was to focus on passenger-owned belongings and distinguish arrest-based searches from probable-cause searches. Tie a vote to the inspected case; do not present that example instruction as a verified legal conclusion.
5. Click **Search again →**. Expand **Search activity · round N** to show the query/action trace and research mode. Show fixed filters, earlier results using **Search round**, and any **New to this matter** badges. In local mode the explicit positive reason changes the query; in model mode verify actual search/read actions rather than assuming feedback caused a useful discovery.
6. Under **Saved cases**, click **↓ Export collection · CSV**, open the file, and compare its rows with the selected cases.
7. Refresh and reopen the matter. Demonstrate retained history, feedback, and selections. Consent resets on refresh; review the mode and reaccept the disclosures before another external round.
8. Change appearance/text size and refresh. Explain that these are explicit preferences; automatic behavioral learning is not implemented.

## Suggested narration outline (adjust to official limit)

- 20 seconds: lawyers need to find cases and inspect why they matter; introduce the local-first workspace.
- 40 seconds: create the synthetic matter, explain limited collection coverage, search.
- 40 seconds: inspect a source passage and save a case independently of relevance.
- 45 seconds: provide feedback, repeat search, inspect action history and unchanged filters.
- 25 seconds: export, persistence, settings.
- 35 seconds: actual implementation status, limitations, and the planned follow-up below.

This totals approximately three minutes and twenty-five seconds. It is not a course-mandated limit. Describe observed live model actions, and label edited wait time or cached inputs. Show no keys, account IDs, private facts, or local credential files in the recording. State that one lead/combined or available opinion is read per case; separate opinions and subsequent treatment are not comprehensively checked.

## Next steps to mention in the demo

> I have a reviewer lined up. Next, I'll prepare a relevance guide and run a walkthrough, checking supporting passages and contrary cases while measuring their time and effort. I'll keep final evaluation judgments separate from search feedback and document a comparison with existing tools. I'll also test basic details for around twenty cases per query instead of up to five, keeping opinion reads capped and comparing relevance, time, and cost.

Keep these items explicitly labeled as future work:

- **Existing-tool comparison:** document the chosen workflow alongside existing products using current official sources; do not claim uniqueness.
- **Review guide and walkthrough:** prepare relevance criteria, document the available reviewer's relevant expertise, and assess usefulness, confusing interactions, and explanation support. Reviewer availability is confirmed; completed review is not.
- **Human effort:** record time spent reading, judging, giving feedback, and correcting explanations, separately from system waiting time and API usage.
- **Independent assessment:** use reserved questions and freeze outputs before final judgments; do not feed those judgments back into the assessed search. Reused demo scenarios are development examples.
- **Contrary-case discovery:** assess whether relevant unfavorable cases are actually found, not just permitted by the agent's instructions.
- **Candidate shortlist:** compare up to five versus approximately twenty candidate metadata records per query without expanding full-opinion reading or source-request budgets.
- **Potential research monitoring:** explore an opt-in **Watch this research** feature for new query matches or citations to saved cases. Begin with email alerts; consider webhook delivery if the additional hosting and reliability work is justified. This remains exploratory and is outside the midpoint scope; see the [monitoring plan](../PROJECT_TODO.md#potential-extension-research-monitoring).

Optional extra closing line, if time permits (about ten seconds beyond the outline):

> Another potential extension is research monitoring: notifying lawyers about new matching cases or citations to their saved cases through CourtListener alerts.

The detailed tasks are in [PROJECT_TODO.md](../PROJECT_TODO.md#next-steps-from-faculty-feedback). These follow-up tasks do not add new midpoint recording prerequisites under the current product plan. Browser rehearsal and repository/video delivery remain open.

Currently, each model search call receives up to five candidate records selected from CourtListener's relevance-ranked results, with available-text and unseen-case preferences. Five is an initial cost/latency setting, not a validated optimum. The planned experiment expands candidate metadata, not full-opinion reading: keep existing reading and request budgets, compare the five- and approximately twenty-candidate settings on the same public questions and filters, and record relevance judgments, newly discovered relevant cases, latency, and model usage/cost where available. Include relevant contrary cases in that assessment. This is future work; no improved relevance or comprehensive search is established.

## Final check

Watch the exported video, verify links/permissions, and record the demonstrated Git commit. Do not mark the submission complete merely because the local workflow works.
