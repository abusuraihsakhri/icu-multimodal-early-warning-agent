# ICU Multimodal Early Warning Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** CAP / CLSI / ISO / PhysioNet / MIMIC-IV Benchmark Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

ICU Multimodal Early Warning Agent is a clinical decision support system that fuses real-time waveform data with laboratory trajectories to detect patient deterioration early. It employs a multi-agent architecture with specialized workers for invariant quality control, safety escalation, and protocol conformance monitoring.

---

## Key Features

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE, ELEVATED, CRITICAL_STAT) with automated clinical action recommendations
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection
- **Zero-PHI Outbound Interceptor**: Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation
- **FastAPI REST API**: OpenAPI 3.1 endpoints with Prometheus telemetry (`/metrics`)
- **Multi-Agent Architecture**: Specialized workers for QC, safety escalation, and protocol conformance

---

## Installation

### Prerequisites
- Python 3.9+
- pip or uv package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/icu-multimodal-early-warning-agent.git
cd icu-multimodal-early-warning-agent

# Install dependencies
pip install -e .

# Install with test dependencies
pip install -e ".[test]"

# Configure environment
cp .env.example .env
# Edit .env and set your AUDIT_SECRET_KEY
```

### Generate a Secure Audit Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Usage

### CLI Commands

#### 1. Single Task Evaluation (Audit)
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### 2. System Configuration Query (Chat)
```bash
python cli.py chat "What is the system status?"
```

#### 3. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

#### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | System configuration query |
| GET | `/api/audit/logs` | Retrieve audit trail |

### Input Data Schema

| Field | Type | Description | Required |
|:------|:-----|:------------|:---------|
| `task_id` | string | Unique task / case identifier | Yes |
| `target_identifier` | string | Entity, patient key, or target | Yes |
| `primary_metric` | float | Primary domain measurement | Yes |
| `secondary_metric` | float | Secondary kinetic/confidence score | No (default: 0.0) |
| `status_descriptor` | string | Status code or phenotype | No (default: "NOMINAL") |
| `is_critical_flag` | boolean | Emergency escalation trigger | No (default: false) |

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=icu_multimodal

# Run specific test file
pytest tests/test_icu_multimodal_early_warning_agent.py -v
```

### Simulation Benchmark

```bash
# Run 1000-task simulation
python simulator.py 1000
```

---

## Docker Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker-compose up --build

# Or use Docker directly
docker build -t icu-multimodal-early-warning-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$AUDIT_SECRET_KEY icu-multimodal-early-warning-agent
```

---

## Architecture

### Multi-Agent System (`agents/`)

| Module | Purpose |
|:-------|:--------|
| `models.py` | Pydantic v2 data models and enumerations |
| `base.py` | PHI guard, HMAC-SHA256 audit trail, security exceptions |
| `workers.py` | Specialized domain workers (QC, Safety, Protocol) |
| `supervisor.py` | Master orchestrator coordinating all workers |
| `api.py` | FastAPI REST endpoints |
| `llm_factory.py` | LLM provider abstraction (mock, Ollama, Claude, OpenAI) |
| `learning.py` | Bayesian calibration and active learning |
| `metrics.py` | Prometheus metrics exporter |
| `streamer.py` | WebSocket telemetry broadcaster |

### ICU Multimodal Module (`icu_multimodal/`)

| Module | Purpose |
|:-------|:--------|
| `models.py` | Dataclass models for frontier payload |
| `engine.py` | Core algorithmic evaluation engine |
| `agents.py` | Specialized sub-agents for waveform/lab fusion |
| `cli.py` | Command-line interface |
| `server.py` | FastAPI server factory |

---

## Security

- **PHI Protection**: All outbound data is inspected against HIPAA Safe Harbor patterns
- **Audit Trail**: Cryptographic chaining prevents log tampering
- **Secret Management**: Audit keys are never hardcoded; must be provided via environment variable
- **Input Validation**: All inputs are validated with Pydantic models

---

## License

MIT License - see [LICENSE](LICENSE) for details.
