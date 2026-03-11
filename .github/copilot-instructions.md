# Copilot instructions — cablemodem (DOCSight fork)

Purpose: quick reference to help automated agents (Copilot CLI, code-review bots) understand how to build, run, test, and navigate this repository.

---

## Quick build / run / test commands

- Setup (local Python dev):

  python3 -m venv .venv && . .venv/bin/activate
  pip install -r requirements.txt

- Run locally (development / manual):

  python -m app.main

- Docker (development):

  docker compose -f docker-compose.dev.yml up -d --build
  - Dev web UI: http://localhost:8767 (demo mode)

- Docker (production / compose):

  docker compose -f docker-compose.yml up -d --build
  - Prod web UI: http://localhost:8765

- Tests (pytest):

  Run full suite:
    python -m pytest tests/ -v

  Run a single test (example):
    python -m pytest tests/path/to/test_file.py::test_function -q

- Linting / formatting:
  No repository-level linter/formatter config was detected (no pyproject.toml, setup.cfg, or .pre-commit-config.yaml to rely on). If a linter/formatter is added, document the commands here.

---

## High-level architecture (big picture)

This project is DOCSight — a modular, collector-based document/metrics app adapted here as `cablemodem`.

Pipeline summary (most important flow):

  Collector Registry → Base Collector (fail-safe) → Analyzer / Storage → Web UI (Flask)

Key components and where to look:
- app/main.py              — entrypoint and the ThreadPoolExecutor polling loop
- app/web.py               — Flask routes and API endpoints (thread-safe state)
- app/collectors/          — collector implementations; base collector enforces fail-safes and locking
- app/drivers/             — modem driver implementations; base driver interface at app/drivers/base.py
- app/modules/             — optional modules that extend functionality without editing core
- app/storage/             — SQLite storage (WAL mode) and storage mixins
- app/i18n/                — translation JSONs (en, de, fr, es)
- templates/ and static/   — Jinja2 templates and static assets
- Dockerfile + docker-compose*.yml — containerized deployment and local dev
- docs/ and ARCHITECTURE.md — deeper design documentation and diagrams

---

## Key conventions and repository-specific patterns

- Collector pattern: new data sources must subclass the Collector base (app/collectors/base.py) and be registered via the collector registry (auto-discovery used by the app).

- Driver pattern: modem drivers implement the ModemDriver base (app/drivers/base.py) and are registered via the driver registry (app/drivers/registry.py). Follow existing drivers as examples.

- Threading & concurrency: collectors run in parallel using ThreadPoolExecutor. Protect shared state with locks and write storage with concurrency in mind (SQLite WAL mode is used).

- Modules: functionality extensions should be implemented as modules under app/modules or the `modules/` directory so core code is untouched; see CONTRIBUTING and the community modules repo linked in docs.

- Internationalization: UI strings live in app/i18n/*.json. When changing UI text, update all active language files (en, de, fr, es) and maintain the `_meta` fields.

- Tests: the test suite is large (1000+ tests). Use pytest. Use the tests/ and tests/e2e/ directories for unit and end-to-end tests. Run the full test suite before opening PRs that change behavior.

- Configuration: app/config.py reads environment variables and config.json; .env.example shows expected env variables. Do not commit secrets — follow repo's security guidance.

- Contributions: open an issue before large/architectural changes (see CONTRIBUTING.md). Small fixes (typos, trivial bugs) can be PR'd directly.

---

## CI and automation notes

- GitHub Actions workflows live under .github/workflows. CI runs the pytest suite and packaging steps—check workflow YAML files for exact steps if you need to reproduce CI locally.

## Files used by AI assistants

- Important docs to reference when generating code or PR text: README.md, CONTRIBUTING.md, INSTALL.md, ARCHITECTURE.md, and docs/*. Use those as the authoritative guides for architecture and contribution rules.

(There were no repository-specific assistant rule files like CLAUDE.md, AGENTS.md, or .cursorrules to incorporate.)

---

If you (or an automated agent) are going to modify core behavior, follow the patterns above and run the full pytest suite. For UI changes, include i18n updates.

---

## MCP servers (Playwright + Podman)

This repository includes a minimal Playwright (Python) E2E setup using Podman pods for local runs and a CI workflow targeting self-hosted runners with Podman installed.

Files added:
- requirements-playwright.txt — Playwright + pytest deps for E2E
- tests/e2e/test_playwright_smoke.py — small Playwright smoke test using the pytest 'page' fixture
- podman-play.yml — Kubernetes pod YAML for use with 'podman play kube' (mounts the repo and runs tests)
- .github/workflows/playwright-podman.yml — CI workflow for self-hosted Podman runners (builds image and runs the pod)

Local run (example):

  # build the app image (required so pod uses local image)
  podman build -t cablemodem:local .
  # run the pod (this YAML mounts the repo path below; update hostPath if different)
  podman play kube podman-play.yml

The Playwright container installs the E2E dependencies and runs pytest against the 'app' service at http://app:8765 by default (BASE_URL env var).

CI notes:
- The included workflow targets self-hosted runners with Podman available. It builds the app image and runs 'podman play kube' using podman-play.yml.
- Ensure the runner has Podman and necessary privileges; adjust timeouts or add readiness checks if your environment needs them.

