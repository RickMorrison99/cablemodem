Local coverage workflow

This repository no longer uploads coverage to codecov.io by default.
CI now generates a coverage XML and an HTML report and uploads them as a GitHub Actions artifact named `coverage-reports`.

Download and view coverage locally

1. In the Actions run that ran the tests, find the `coverage-reports` artifact and download it from the web UI, or use the gh CLI:

   gh run download <run-id> --name coverage-reports -R RickMorrison99/cablemodem

   This will create a zip containing `coverage.xml` and the `htmlcov/` directory.

2. Unzip and serve the `htmlcov/` directory locally. Two ways:

   - Using the provided script (recommended):

     ./scripts/run_coverage_server.bash path/to/htmlcov [port]

     Example: ./scripts/run_coverage_server.bash htmlcov 8000

   - Using docker directly:

     docker run --rm -p 8000:8000 -v "$(pwd)/htmlcov":/srv -w /srv python:3.11-slim python -m http.server 8000

3. Open http://localhost:8000 in your browser to browse the coverage HTML report.

Notes

- Artifacts are ephemeral and tied to a workflow run. Re-run the workflow to regenerate.
- If you prefer a persistent coverage dashboard, run your own hosted coverage service reachable from CI instead (more setup required).
