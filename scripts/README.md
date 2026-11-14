# Development Scripts

## Save and check a CourtListener token

**Current project status:** token setup is complete. The initial authenticated probe returned 20 results and one linked 31-character record. Subsequent application checks retrieved full opinions and passed a feedback-driven model round, exact-text verification, export, and request-idempotency checks. Do not rerun setup merely to use the app. Browser and professional legal validation remain open. The setup instructions below are for a fresh installation or intentional credential replacement.

In a new local Terminal window, run from the project root:

```bash
.venv/bin/python scripts/configure_courtlistener.py
```

Paste the token at the hidden prompt and press Enter; no characters will appear. The command saves only the CourtListener setting to ignored `.env.local`, preserves the existing OpenAI configuration, and restricts the file to its owner. It then checks a public automobile query and one full opinion (at most two requests, no model calls). The sanitized result is saved to `data/courtlistener-auth-check.json`.

A failed check does not remove the saved token; use the safe status/error category to diagnose access. Do not paste the token into chat or a shell command. This script checks access separately from the now-implemented application source adapter. It does not exercise model-assisted research or the browser workflow.

## Use the broader source in the application

Restart with Start-Casework.command or `.venv/bin/python scripts/start_local.py --open`, and use the URL it opens. Create a new matter with **CourtListener · broader U.S. case search**. Existing matters retain their original source; restarting does not silently widen their scope. The source offers all available U.S. courts or specific SCOTUS/federal-circuit filters, dates from 1600 through today, and a UI default of 1900 through today. The vehicle/container demonstration topic and six offline fixtures do not restrict live-source research questions.

Source queries require the CourtListener consent checkbox. Optional model analysis additionally requires the OpenAI consent checkbox. With model assistance off, the app performs a visible keyword search and retrieves source excerpts without generating a legal interpretation. Optional search terms can refine the query. Live source and model integration checks passed through the API; browser validation is still pending.

The saved real-run reports are `data/live-source-checks/first-source-round.json` and `data/live-source-checks/model-feedback-round.json`. The first query reported 2,851 matches and retrieved three full case/opinion records. The model follow-up returned three new cases with nine checked excerpts in 25.2 seconds, using five model calls, four tools, four source requests, 20,942 input tokens, and 517 output tokens; export and request-idempotency checks passed. These reports are ignored local artifacts and are not bundled fixtures or a claim of legal correctness.

Each round uses at most four uncached CourtListener requests. The app maintains a persistent local allowance of 5/minute, 50/hour, and 125/day; these match the observed account-usage response. Provider 429 responses still take precedence. Cached reads cost no source API request, and source limits remain separate from model-call limits.

`data/courtlistener-cache.sqlite3` stores query-bearing search URLs, public case metadata, opinion snapshots, and the rate ledger. Search responses expire after 24 hours and are refetched when requested. Confirmed missing-text responses are also cached for 24 hours before another read can recheck them. Positive opinion snapshots persist indefinitely; opinion-update checking and cache cleanup controls are not implemented. Deleting a matter does not delete its shared cache. Do not remove the cache to bypass the request allowance.

## CourtListener access probe

`validate_courtlistener.py` checks a small real search and linked opinion text. It is separate from the application, uses Python's standard library, and does not call an LLM. Run from the project root.

For authenticated validation, obtain your own token from [CourtListener's token page](https://www.courtlistener.com/profile/api-token/), then enter it at the hidden terminal prompt:

```bash
.venv/bin/python scripts/validate_courtlistener.py --prompt-token --output data/courtlistener-auth-check.json
```

Alternatively, the script reads an already configured `COURTLISTENER_API_TOKEN` environment variable when `--prompt-token` is omitted. This probe does not load `.env`. Do not paste tokens into chat, command arguments, source files, or reports. The single-server app launcher separately loads allowlisted OpenAI and CourtListener configuration from `.env.local`.

An explicit unauthenticated network diagnostic is available:

```bash
.venv/bin/python scripts/validate_courtlistener.py --anonymous --output data/courtlistener-anonymous-check.json
```

Defaults: keyword `automobile`, court `scotus`, decision dates 1980-01-01 through 2020-12-31, one search page and at most two opinion fetches. Add `--pages 2` to exercise the returned next cursor when available (at most four total requests). `--max-opinions 1` reduces the text sample. The script checks returned court/date constraints, separate cluster/opinion IDs and their relationship, source links, safe pagination, and nonempty opinion text. It prefers `html_with_citations`, then `plain_text`; other text formats are not parsed by this diagnostic.

Reports store public metadata, text-field names, lengths/hashes, and fixed error categories under ignored `data/`; raw text, response bodies, and credentials are omitted. Redirects are rejected before following them. There are no retries. This is a small sample, not a coverage audit or quotation validator. An unchanged `next` cursor beyond the requested page budget is left unvisited.

`passed` means the authenticated sample succeeded; `anonymous_access_only` cannot establish account access. `blocked` or `partial` exits with code 1; inspect the report's stage/category. A missing token makes zero requests. On 401/403 check credentials/entitlements; on DNS failure use an environment that can reach the source; on 429 stop and wait for the applicable allowance. The standalone script does not manage rolling quotas across runs or contribute to the application's local rate ledger. Check your account's actual allowance and avoid repeated back-to-back probes; the observed account limits here are 5/minute, 50/hour, 125/day.

Offline verification:

```bash
.venv/bin/python -m pytest backend/tests -q
```

`test_courtlistener_probe.py` uses synthetic injected responses. It tests filter/identity failures, missing text, hostile pagination, credential-safe errors, and request budgets. It makes no network calls. See [DATA_SOURCE.md](../docs/DATA_SOURCE.md) for the actual live checks and blockers.

## Local official-PDF corpus

Run `.venv/bin/python scripts/import_demo_corpus.py` to download/extract the six allowlisted PDFs. Original PDFs, hashes, and extracted page text go to ignored `data/corpus/`. Cached PDFs avoid repeated downloads; results are actual source text, not mock responses. `pypdf` and `fonttools` are runtime dependencies.

Run `.venv/bin/python scripts/smoke_local_workspace.py` for the real-source HTTP walkthrough with a disposable SQLite database on port 8011. It makes no model calls and writes a safe report under `data/`. `serve_e2e.py` supports Playwright with another disposable workspace and model access disabled.

## Opt-in live model check

`python scripts/validate_live_agent.py --live` runs one bounded model-assisted purse-scenario check against the **local official-PDF corpus**, using the confirmed `.env.local` or environment configuration. It sends public synthetic facts and official source excerpts to OpenAI and may incur API charges. Reports go to ignored data/live-checks; raw provider errors and credentials are never printed. Without --live, no request is made. This is separate from the no-model HTTP smoke test and the completed CourtListener application checks recorded above; the local-PDF script alone does not test live source integration.
