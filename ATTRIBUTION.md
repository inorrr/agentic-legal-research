# Attribution and External Resources

Individual project by Yinuo Zhao. The author is responsible for understanding and explaining the system.

OpenAI ChatGPT/Codex assisted with brainstorming, documentation, architecture, application implementation, source integration, tests, and debugging. Engineering checks are recorded in docs/VALIDATION.md; they are not professional legal validation.

Used libraries include React, TypeScript, Vite, FastAPI, Pydantic, HTTPX, pytest, python-dotenv, and Python's SQLite module. The OpenAI SDK adapter and CourtListener application adapter are implemented and live-verified on a public synthetic scenario. pypdf and FontTools support official-PDF extraction. Playwright supports browser tests (launch blocked in this environment). Record resolved versions and their licenses with dependency locks before release.

Sources consulted for technical planning:

- Vite setup: https://vite.dev/guide/
- FastAPI setup: https://fastapi.tiangolo.com/tutorial/first-steps/
- CourtListener search API: https://wiki.free.law/c/courtlistener/help/api/rest/v4/search
- OpenAI credential guidance: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
- OpenAI billing: https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform

Faculty feedback is preserved in feedback_abel.md and feedback_John.md. Add provenance and reuse permission for each future dataset, fixture, excerpt, or external code contribution. An application license does not license third-party data. No third-party application code was copied into this scaffold.

During the initial 2026-11-13 source investigation, ChatGPT/Codex assisted with primary-source inspection, topic selection, an access probe, and synthetic offline tests. Six factual seed records link to official U.S. Reports PDFs at GovInfo/Library of Congress; three demonstration scenarios are original synthetic examples. Their provenance and limitations are recorded in docs/DATA_SOURCE.md and examples/vehicle_search/. No commercial headnotes, redistributed full-text dataset, credentials, or expert legal labels were added to distributable project content.

Later that day, authenticated CourtListener integration and three live application rounds were verified. CourtListener / Free Law Project supplies live case metadata and opinion records. Locally cached source text retains case/opinion identities, source links, extraction kind, timestamps, and hashes; it is stored under ignored data paths rather than bundled with the source code. CourtListener text sections are local navigation units, not original reporter pinpoints. Source access and reuse terms remain separate from the future application license.

Official OpenAI documentation used for the optional adapter:
- https://developers.openai.com/api/docs/guides/function-calling
- https://developers.openai.com/api/docs/guides/structured-outputs

Official PDFs downloaded for local use retain source provenance in the ignored corpus index; they are not bundled into source control. Copied syllabus/headnote collections from commercial services are not included. Development checks include synthetic model/source fixtures, clearly separated from real PDF retrieval.

Initial configured model: GPT-4.1 mini (runtime choice, not a legal-quality endorsement). Documentation: https://developers.openai.com/api/docs/models/gpt-4.1-mini . Local configuration uses python-dotenv; HTTPX includes SOCKS support.
