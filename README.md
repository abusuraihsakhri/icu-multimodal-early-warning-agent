# ICU Multimodal Early Warning Agent

A Python threshold-classification prototype with a browser-only demonstration. It evaluates two **unitless example metrics**, a descriptor, and an optional manual critical flag. Outputs are deterministic alerts, **not clinically validated early-warning scores**.

> **Research/educational software only.** The repository does not ingest raw ICU waveforms, calculate laboratory trajectories, implement a trained deterioration predictor, or provide validated clinical recommendations. Do not use for patient care.

## Implemented components

- **agents/** — main CLI and FastAPI service. Alerts when primary >25, secondary >12, critical override is selected, or the descriptor contains DISCORDANT, ANOMALY, MUTANT, VIOLATION, FAIL, or REJECT. Critical override takes precedence.
- **icu_multimodal/** — separate legacy example with secondary threshold >10. It is not identical to the main service.
- **enrichment.py** — generic threshold classes, not clinically validated ventilation, vasopressor, sepsis, nutrition, or sedation algorithms.
- **web/** — static JavaScript implementation of the main three-worker rule set. No Python service, clinical prediction, audit signing, or backend calls occur on the page.

No external language-model provider is implemented. The chat command returns a deterministic mock response.

## Browser demonstration

Open web/index.html locally. Enter **synthetic**, non-identifying sample keys and metrics, select **Evaluate example**, and optionally export a JSON result. Nothing entered is uploaded or persisted by the static app. It is not a PHI de-identification service.

## Install and run Python

Python 3.10–3.12 is tested in CI (package metadata supports 3.9+).

    git clone https://github.com/abusuraihsakhri/icu-multimodal-early-warning-agent.git
    cd icu-multimodal-early-warning-agent
    python -m pip install -e ".[test]"
    export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

Generate a unique audit secret for each deployment. Python reads environment variables directly; it does not automatically load .env files.

    python cli.py audit --task-id DEMO-1 --target SYNTHETIC-1 --primary 28.5 --secondary 14.2
    python cli.py batch -i sample.csv -o results.csv
    python cli.py verify-audit
    python cli.py chat "What is the status?"
    python cli.py serve --host 127.0.0.1 --port 8000

Batch CSV input includes task_id, target_identifier, primary_metric, secondary_metric, is_critical_flag, and status_descriptor. Boolean flags accept true/false, yes/no, and 1/0, case-insensitive.

## HTTP API

| Method | Path | Purpose |
|---|---|---|
| GET | /health | Health |
| POST | /api/audit | Evaluate synthetic inputs |
| POST | /api/chat | Deterministic mock response |
| GET | /metrics | Prometheus text |
| GET | /api/audit/logs | Audit metadata, disabled without a token |
| GET | /openapi.json | Generated OpenAPI schema |

Set a distinct, high-entropy AUDIT_LOGS_TOKEN and pass an Authorization: Bearer token header to enable audit metadata reads. The audit endpoint is disabled without this setting. Do not expose the service to untrusted networks without appropriate authentication, TLS and operational controls.

## Security and privacy

- HMAC-SHA256 signs an in-memory chain of audit metadata. The verifier checks the signatures and links; the trail is **not persistent** and disappears on restart.
- Regex PHI screening is **incomplete** and does not demonstrate HIPAA Safe Harbor de-identification. Do not process actual patient records.
- Evaluations are not rate-limited or authenticated by default. Use only locally or within a properly secured environment.
- The browser demo uses only local JavaScript, DOM text nodes, and a user-triggered JSON download. It does not use network calls or browser storage.

## Tests

    python -m pytest -q
    python -m compileall -q agents icu_multimodal cli.py enrichment.py
    python -m pip check
    node --check web/app.js
    node --test tests/web.test.cjs

GitHub Actions tests Python 3.10–3.12 and the browser rule set. The web demonstration requires a modern JavaScript-enabled browser. GitHub Pages can host only the static demo; the FastAPI service requires Python hosting.

## Docker

    export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
    docker compose up --build

Compose binds to localhost:8000 by default.

## License

[MIT](LICENSE).
