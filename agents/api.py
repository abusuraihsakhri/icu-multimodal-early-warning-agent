"""
FastAPI REST API Server for Icu Multimodal Early Warning Agent.
"""
import hmac
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from .metrics import GLOBAL_METRICS
from .base import SecurityException
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Icu Multimodal Early Warning Agent API",
    description="Non-clinical demonstration of deterministic threshold alerts. Not validated for patient care.",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "icu-multimodal-early-warning-agent", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return PlainTextResponse(GLOBAL_METRICS.export_prometheus_text(), media_type="text/plain; version=0.0.4")


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        GLOBAL_METRICS.record_phi_block()
        raise HTTPException(status_code=422, detail="Input contains a potentially identifying value.")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        GLOBAL_METRICS.record_phi_block()
        raise HTTPException(status_code=422, detail="Input contains a potentially identifying value.")


@app.get("/api/audit/logs")
def api_audit_logs(authorization: Optional[str] = Header(default=None)):
    expected_token = os.getenv("AUDIT_LOGS_TOKEN", "")
    if not expected_token:
        raise HTTPException(status_code=403, detail="Audit log API is disabled.")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not hmac.compare_digest(supplied, expected_token):
        raise HTTPException(status_code=401, detail="Authentication required.")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
