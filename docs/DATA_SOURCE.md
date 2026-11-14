# Case sources, coverage, and access validation

Validation date: **2026-11-13**. This records source inspection and engineering checks, not professional legal validation.

## Latest status — broader source integration

CourtListener credentials are now configured locally. The user's authenticated access probe passed with **20 search results and one linked record containing 31 text characters**. This verifies authenticated search and record retrieval; the short record is not proof of substantive reasoning, complete opinion coverage, or legally useful results. The account-usage endpoint reported limits of **5 requests/minute, 50/hour, and 125/day**.

The application now implements CourtListener search and lazy opinion retrieval through `backend/src/legal_research/courtlistener.py`, with a keyword-only path in `source_search.py` and source-aware model tools. **Expanded API integration has passed real source and model checks:** the first source round reported 2,851 matches for its query and retrieved three full case/opinion records; the next model-assisted round used saved feedback and returned three new cases. The reported match count describes that query, not the total size or completeness of CourtListener.

The model round took 25.2 seconds with five model calls, four tool calls, four uncached source requests, 20,942 input tokens, and 517 output tokens. Nine excerpts were checked against exact stored opinion-text slices. Export and repeated-request idempotency also passed. Reports: `data/live-source-checks/first-source-round.json` and `data/live-source-checks/model-feedback-round.json`. Browser operation, broader relevance quality, and professional legal validation remain unverified; see VALIDATION.md.

**Current scope:** the product searches available U.S. case law within each user's court/date filters. Fourth Amendment vehicle and container searches are the selected demonstration topic. The six official PDFs support offline regression checks and a fallback demonstration; they are not a permanent topic or database restriction for CourtListener matters.

New matters can choose **CourtListener · broader U.S. case search**. The court filter offers all available U.S. courts, SCOTUS, or a listed federal appellate circuit. The server accepts date filters from 1600 through today; the UI defaults to 1900 through today. “All available” means the provider's indexed collection, not complete U.S. case law. Court/date filters remain fixed within a matter. Existing six-case matters retain the local source, court, dates, and history; create a new matter to use broader search.

Each round allows at most four uncached source requests. The separate persistent cache/ledger, normally `data/courtlistener-cache.sqlite3`, conservatively enforces 5/minute, 50/hour, and 125/day across application rounds. Other programs and standalone access probes are not included in that local ledger. Provider 429 responses remain authoritative and record a waiting period. Unlimited user-started rounds are supported within these per-round and account limits; the app does not rotate keys or discard the ledger to evade them.

Search results are cached for 24 hours and refetched on a later request after expiry. Confirmed missing-text records are also cached for 24 hours, then may be checked again on a later read. Positive opinion snapshots persist indefinitely; automatic update checks, opinion refresh, and cache-eviction controls are not implemented. The cache includes query-bearing search URLs and public source text. Deleting a matter does not erase this shared cache. An updated search response does not establish that a previously cached opinion snapshot is current.

The adapter checks cluster/opinion relationships and retrieves one lead/combined or otherwise available opinion per case. Other separate opinions are not automatically loaded. HTML is converted to documented canonical text; excerpts are exact slices of the retained representation, with source links, opinion IDs/types, hashes, and offsets. The UI labels local **text sections** rather than inventing PDF or reporter pages. Short records are labeled; search rank and exact text matching do not establish relevance or a legal holding. Subsequent treatment is not checked, and the app makes no automatic “good law” assertion.

Source-query consent is separate from model consent. CourtListener queries can contain terms derived from the user's question or feedback; OpenAI receives the disclosed matter/context and selected passages when model assistance is enabled. The six official PDFs remain an offline test/demo collection. The following sections retain the original scope and access history; the latest status above supersedes their earlier missing-token and not-yet-implemented observations.

## Original demo decision (historical)

Start with **Fourth Amendment warrantless vehicle and container searches**, using **U.S. Supreme Court decisions issued from 1980-01-01 through 2020-12-31**. The initial six cases below are seed examples, not an exhaustive collection. CourtListener remains the intended search source. Official U.S. Reports PDFs from GovInfo and the Library of Congress provide independently inspectable primary text for the seeds.

This topic supports useful factual comparisons: arrest versus a traffic citation, suspicion concerning a car versus one bag, passenger ownership, and a vehicle within a home's protected surroundings. Both search-permitting and search-limiting cases belong in relevant results. These distinctions are easier to demonstrate in a small product than broad qualified-immunity research, which would add separate constitutional and immunity questions.

The date window is a historical demonstration boundary. It is **not complete current law**. Earlier authorities, later decisions, federal appellate applications, state constitutional protections, and other search exceptions are outside this initial collection. References to out-of-scope cases must be labeled; following a citation must not silently widen the user's filters. Do not describe a case as still good law without a separately verified basis.

## Initial access observations (historical)

| Check | Observed result | What it establishes |
| --- | --- | --- |
| Official primary PDFs | All six URLs below opened through the research web tool; full opinion text was available beyond the syllabus | A real, readable primary source exists for each seed; this is not a local downloader or API integration test |
| CourtListener public index | [Volume 556](https://www.courtlistener.com/c/us/556/) lists Gant, 556 U.S. 332, 2009-04-21, docket 07-542, and its case link | Public metadata and a case/cluster URL can be identified |
| CourtListener opinion page | [Gant case page](https://www.courtlistener.com/opinion/145887/arizona-v-gant/) returned a JavaScript/anti-bot screen | Full text was not retrieved from this page; do not scrape around the challenge |
| Backend-network probe | Python request to CourtListener v4 search failed with DNS resolution error before an HTTP response | This execution environment did not reach the API; no conclusion about API authentication or search results follows |
| Credentials | `COURTLISTENER_API_TOKEN` absent; no project `.env` exists | Authenticated access was not tested; no account was created or modified |
| Browser fallback | In-app browser session failed to attach its new tab | No browser-based API or opinion verification was completed |

**Status at this historical checkpoint:** the data-path gate was still open. Public primary-text access had been verified, but authenticated CourtListener query → results → opinion text and local network access had not. The later successful source/model checks are recorded above. Search recall and collection completeness remain unmeasured.

## Six verified seeds

Dates are decision dates. PDF page counts include syllabi and separate opinions. Pinpoints below refer to printed U.S. Reports pages in the Court's opinion, not a syllabus or dissent.

| Case and decision date | Docket | Primary source / PDF pages | Comparison to exercise; majority pinpoint |
| --- | --- | --- | --- |
| United States v. Ross, 456 U.S. 798 (1982); 1982-06-01 | 80-2209 | [LOC PDF](https://tile.loc.gov/storage-services/service/ll/usrep/usrep456/usrep456798/usrep456798.pdf), 46 pages | Probable cause and the places/containers capable of holding the object of the search; pp. 824–825 |
| California v. Acevedo, 500 U.S. 565 (1991); 1991-05-30 | 89-1690 | [GovInfo PDF](https://www.govinfo.gov/content/pkg/USREPORTS-500/pdf/USREPORTS-500-565.pdf), 38 pages | Suspicion confined to a particular bag does not automatically justify searching the entire car; pp. 579–580 |
| Knowles v. Iowa, 525 U.S. 113 (1998); 1998-12-08 | 97-7597 | [GovInfo PDF](https://www.govinfo.gov/content/pkg/USREPORTS-525/pdf/USREPORTS-525-113.pdf), 7 pages | A traffic citation without arrest did not itself justify the full vehicle search; pp. 114–119 |
| Wyoming v. Houghton, 526 U.S. 295 (1999); 1999-04-05 | 98-184 | [GovInfo PDF](https://www.govinfo.gov/content/pkg/USREPORTS-526/pdf/USREPORTS-526-295.pdf), 19 pages | Passenger belongings capable of holding the object of a probable-cause vehicle search; p. 307 |
| Arizona v. Gant, 556 U.S. 332 (2009); 2009-04-21 | 07-542 | [GovInfo PDF](https://www.govinfo.gov/content/pkg/USREPORTS-556/pdf/USREPORTS-556-332.pdf), 34 pages | Search incident to arrest: access to the car and evidence of the arrest offense; other exceptions remain distinct; pp. 343–344, 351 |
| Collins v. Virginia, 584 U.S. 586 (2018); 2018-05-29 | 16-1027 | [GovInfo PDF](https://www.govinfo.gov/content/pkg/USREPORTS-584/pdf/USREPORTS-584-586.pdf), 31 pages | The automobile exception did not authorize entry into the home's curtilage to reach a motorcycle; another justification remained for remand; pp. 594–596, 601 |

The initial source-viewer development used the small official-PDF collection, with **Knowles** its shortest PDF. These are authentic judicial documents, not generated case text. Machine-readable seed metadata and three original synthetic matters are in [seed_cases.json](../examples/vehicle_search/seed_cases.json) and [scenarios.json](../examples/vehicle_search/scenarios.json). Expected matches are engineering examples, not a legally reviewed answer key. **The user confirms a reviewer is available; relevant expertise and review findings remain to be recorded.**

## API contract and initial design notes

These initial contract notes came from documentation. The SCOTUS/1980–2020 parameters below describe the original probe, not the new application's full allowed scope. The latest access observations are recorded at the top of this document.

- [Search API](https://wiki.free.law/c/courtlistener/help/api/rest/v4/search): `type=o` returns clusters with nested opinions. Keep `court=scotus`, `filed_after=1980-01-01`, and `filed_before=2020-12-31` explicit. Check returned court/date fields; do not trust a server to enforce filters silently. Search snippets are not full text. Record the response's `next` cursor rather than constructing pages. A returned link must remain on the expected HTTPS API endpoint before credentials are sent.
- [Case-law API](https://wiki.free.law/c/courtlistener/help/api/rest/v4/case-law): use cluster identity for case deduplication and distinct opinion identity for passages. Website `/opinion/145887/...` uses a **cluster** ID; it is not evidence that API opinion 145887 is the right text. Obtain opinion IDs from search `opinions[].id` or cluster `sub_opinions`, then retrieve `/api/rest/v4/opinions/{id}/`. Prefer `html_with_citations`; use nonempty alternative text fields if necessary and record which field supplied text. Preserve opinion type, including combined/unknown types.
- [REST authentication and limits](https://wiki.free.law/c/courtlistener/help/api/rest/v4/rest-api-v47): programmatic authentication uses `Authorization: Token …`. Published defaults are **5 requests/minute, 50/hour, 125/day**, concurrently enforced. Account-specific limits must be checked through the [usage API](https://wiki.free.law/c/courtlistener/help/api/rest/v4/api-usage). Stop on 429 and honor retry guidance; do not rotate credentials to avoid limits.

A small probe cannot establish complete topic coverage or all edge cases. On a successful run, inspect stable cluster/opinion IDs, citation, court, decision date, source URL, nonempty full text, and any pagination link. Subsequent adapter work must test missing/null fields, multiple opinion types, duplicate clusters, and source updates.

## Terms, privacy, and text handling

CourtListener's [terms](https://wiki.free.law/c/terms/courtlistener/courtlistenercom-terms-of-service-and-policies) address automated clients, prohibit credential sharing and limit evasion, and require honest attribution when displaying data. They direct product/team access questions to Free Law Project. This review does not establish an account's entitlements or blanket redistribution permission. Before public distribution, resolve any product-access arrangement; do not bundle a shared token or CourtListener dataset. Label AI explanations separately from source material.

The current search documentation says API queries are logged by default, with an account setting to disable logging. Therefore local-first must not imply private/offline searching. Initial probes use only public keywords. The application now requires separate source-query and model-data consent disclosures.

[GovInfo's reuse policy](https://www.govinfo.gov/about/policies) distinguishes U.S. Government works from embedded third-party copyrighted material. Seed fixtures contain factual metadata and original scenarios/summaries, not commercial headnotes, briefs, or copied collections. The cited sources are official judicial opinions. Any later redistributed excerpts need source and page attribution; an application license does not license unrelated source content.

PDF extraction visibly includes broken words and OCR errors. Keep original files/text separate from normalized display/search text. Store source URL, retrieval time, content hash, opinion identity, and printed/PDF page mapping. Do not repair a quotation invisibly. Page headers can name a concurrence that begins later on the same page: segment by the opinion's actual start/end, not headers alone. Sanitized plain text is suitable for the initial source viewer; do not render untrusted source HTML directly.

## Original access-gate procedure (historical)

Use [the validation script](../scripts/validate_courtlistener.py) as documented in [scripts/README.md](../scripts/README.md). It is a development probe, not an implemented application adapter. Results belong under ignored `data/`; no tokens or full opinions are included in its audit report. Offline tests use deliberately synthetic responses and must never be labeled real integration tests.

The original next step was to run an authenticated probe from an environment with network access and a personal CourtListener token, then inspect linked text and account allowance before integrating it. That access step is now complete, and the application has passed the real source/model rounds described above. The standalone probe remains available for future installation diagnostics; the current user does not need to obtain or configure another token.

The six official PDFs were selected as a fallback while access was blocked. Their downloader/importer and local retrieval are now implemented; that fallback must still be labeled separately from live CourtListener search.

## Update: real local corpus import and retrieval — 2026-11-13

The documented official-PDF fallback is now implemented. Direct Python downloads from GovInfo/LOC succeeded for all six cases: **175 PDF pages and 378,221 extracted characters**. The original PDFs and page-text index are under ignored `data/corpus/`. Reproduce with `python scripts/import_demo_corpus.py`. PDF page counts are checked against seed metadata; hashes, source URLs, exact extracted text, and conservative opinion-scope labels are retained. pypdf plus FontTools handles text extraction; no OCR text is silently repaired.

Three complete synthetic matters were exercised through a real local HTTP server: retrieval, quote substring checks, feedback, repeat search, CSV export, and backend restart. See VALIDATION.md. This historical check closed the local fallback data path only; later CourtListener validation is recorded above. It did not establish pagination coverage or legal quality. The earlier DNS observation describes that earlier probe, not an assertion that current outbound access fails.

## Expansion priority and renewed access check — 2026-11-13

Historical checkpoint before the user configured a token; current access and implementation status are at the top of this document.

The user identified six cases as insufficient for useful discovery. This led to the now-implemented live source search with locally cached, attributable opinion text. The six cases remain reproducible fixtures. Court/date restrictions remain explicit user filters, rather than permanent six-case application limits. Search candidates provide metadata first; full text is fetched when read. Pagination and prior-round identities support continued discovery within unchanged filters.

Rechecked the official v4 search, case-law, coverage, and authentication documentation. The initial renewed probe with `--anonymous --max-opinions 1` made **one search request that reached CourtListener and returned HTTP 401** (`authentication_required_or_invalid`). No opinion text was fetched and no token was configured at that time. Report: `data/courtlistener-expansion-access-check.json` (ignored). This replaced the earlier DNS observation, before the later successful authentication and account-limit checks.

CourtListener documents token access through https://www.courtlistener.com/profile/api-token/ and default rolling limits of 5/minute, 50/hour, and 125/day. Validate the actual account allowance before planning multi-round throughput. Unlimited user-started rounds in the app do not override upstream limits. Never bundle shared credentials in the open-source distribution.
