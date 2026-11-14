# Development Guide

Start with README setup commands. Backend code uses the `src` layout and an editable install. The Vite development server uses port 5173; the single-server launcher instead selects a free port from 5173–5183. No credentials are needed for the six-case local demo. CourtListener search and OpenAI analysis need their respective configured access and separate explicit consent.

## Structure

- `backend/src/legal_research/`: API, workspace persistence, source adapters, and bounded model loop.
- `backend/tests/`: backend behavior and adapter tests.
- `frontend/src/`: React UI and styles.
- `docs/`: architecture, decisions, validation notes, and handoff log.
- `data/`: ignored runtime state; only its README is tracked.
- `scripts/`: private token setup, bounded live probes, importer, launcher, and validation utilities.

Add `api/`, `domain/`, `storage/`, `sources/`, `providers/`, and `agent/` modules as their behavior is implemented rather than creating empty abstractions. Keep retrieval/model adapters injectable for offline tests. Never label mocked adapter output as live data.

Current boundaries: `corpus.py` owns the local PDF demo; `courtlistener.py` owns live discovery/cache and source budgets; `source_search.py` handles source-only keyword rounds; `research_agent.py` handles bounded model search/read/evidence selection; `workspace.py` stores matters and their immutable round snapshots. `main.py` enforces scope, consent, local-request safeguards, idempotency, and routes. New live matters use `source=courtlistener`; older records without a source remain local. Avoid silent conversion.

## Configuration

`.env.example` documents supported names. The single-server launcher reads project-root `.env.local` only inside its backend process; existing environment variables take precedence. Only OPENAI_API_KEY, OPENAI_MODEL, COURTLISTENER_API_TOKEN, and LEGAL_RESEARCH_DATA_DIR are loaded. Variable interpolation is disabled and symlink config files are rejected. The example file is never loaded. Direct Uvicorn development requires environment configuration or explicit `--env-file .env.local`. Frontend environment variables are public bundle content and must never contain secrets. Restart the server after changing backend configuration.

## Dependency policy

Manifests express compatible ranges. `frontend/package-lock.json` records the npm resolution; `backend/requirements-dev.lock` records exact installed Python dependency versions (without hashes), resolved on macOS arm64 / Python 3.14. Use the locked commands in README. Verify Python 3.12 and other platforms before claiming support; this is not a cross-platform lock guarantee. Regenerate both when intentionally updating dependencies. Keep tools in the project virtual environment; do not alter global Python packages.

## Workflow

Read AGENTS.md and the latest development log. Take the next unchecked task, build one useful slice, run checks appropriate to the change, and update implementation status and log. Test behavioral boundaries such as filters, state isolation, credential handling, and exports rather than mirroring trivial implementation details.

The directory is intended to become its own repository, separate from the course assignment repository mentioned in faculty feedback. Do not use that URL as the application remote. Publishing, release creation, and course submission are separate actions.

## Git initialization

The environment blocked writing `.git` during scaffolding. Run `git init -b main` from this directory in your local terminal before committing. No remote is configured and nothing has been published.

## Current checks and demo

Read docs/VALIDATION.md and docs/MIDTERM_WALKTHROUGH.md. The local-PDF HTTP smoke script uses port 8011 and disposable state. Playwright tests use ports 8000/5173 and a disposable workspace with both model and CourtListener credentials removed; stop running dev servers before testing. Browser launch was blocked in this execution environment, so browser verification needs a compatible local session. Offline backend tests and frontend `test:transport` / `test:source` make no live provider calls. Do not rerun paid or quota-consuming checks merely because documentation changed.

## Stable local demo launch

Use `python3 scripts/start_local.py` (or Start-Casework.command on macOS) for a single server serving built assets and API, starting at 127.0.0.1:5173 and choosing the next free port if needed. Keep the terminal open. Two-process Vite development remains available; do not run both modes on 5173 simultaneously. `npm run test:transport` runs network-recovery tests without a browser.
