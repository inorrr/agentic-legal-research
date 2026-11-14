# Local Runtime Data

Future SQLite databases and permitted source caches belong here during development. All contents except this README are ignored by Git. Do not store API keys here. No database or case corpus is created by the scaffold. Use public/synthetic examples for demonstrations.

The standalone CourtListener probe writes local audit JSON here. Reports contain configuration/network status and, if retrieval succeeds, public case metadata and text hashes/lengths; no tokens or full opinion text. The 2026-11-13 anonymous diagnostic recorded DNS failure, and the authenticated check recorded a missing token without making a request. Neither is a passing integration run. Shareable seed metadata and synthetic scenarios live under examples/vehicle_search/.
