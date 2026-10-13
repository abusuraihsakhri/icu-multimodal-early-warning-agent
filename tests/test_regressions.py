"""Regression checks for cryptographic integrity, API validation and CSV parsing."""
import csv
import os

os.environ.setdefault("AUDIT_SECRET_KEY", "test-only-audit-secret")
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.api import app
from cli import main, parse_csv_bool


def test_hmac_detects_tampering():
    audit = AuditTrail(secret_key="test-secret")
    audit.log("actor", "tier", "EVENT", {"data": 1})
    audit.log("actor", "tier", "EVENT", {"data": 2})
    assert audit.verify_integrity()
    audit.logs[0]["actor"] = "forged"
    assert not audit.verify_integrity()


def test_hmac_detects_changed_signature_and_ledger_snapshots():
    audit = AuditTrail(secret_key="test-secret")
    audit.log("actor", "tier", "EVENT", {"data": 1})
    audit.get_trail()[0]["current_hash"] = "forged"
    assert audit.verify_integrity()
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_numbers_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="K", primary_metric=value)


def test_identifier_length_limit():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T" * 129, target_identifier="K", primary_metric=1)


def test_nested_attribute_phi_screening():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(task_id="T", target_identifier="K", primary_metric=1,
                                attributes={"nested": {"value": "MRN-12345678"}})
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_api_metrics_phi_and_audit_log_auth(monkeypatch):
    client = TestClient(app)
    ok = client.post("/api/audit", json={"task_id": "T", "target_identifier": "KEY", "primary_metric": 1})
    assert ok.status_code == 200
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "text/plain" in metrics.headers["content-type"]
    assert "system_tasks_total" in metrics.text
    blocked = client.post("/api/audit", json={"task_id": "T", "target_identifier": "MRN-12345678", "primary_metric": 1})
    assert blocked.status_code == 422
    monkeypatch.delenv("AUDIT_LOGS_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 403
    monkeypatch.setenv("AUDIT_LOGS_TOKEN", "read-only-test-token")
    assert client.get("/api/audit/logs").status_code == 401
    authed = client.get("/api/audit/logs", headers={"Authorization": "Bearer read-only-test-token"})
    assert authed.status_code == 200
    assert authed.json()["verified"] is True


@pytest.mark.parametrize("raw,expected", [("False",False),("0",False),("true",True),(" YES ",True),("",False)])
def test_csv_critical_boolean(raw,expected):
    assert parse_csv_bool(raw) is expected


def test_csv_false_not_critical(tmp_path):
    source = tmp_path / "inputs.csv"
    target = tmp_path / "results.csv"
    source.write_text("task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\n"
                      "A,K,0,0,False,NOMINAL\n", encoding="utf-8")
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(encoding="utf-8",newline="") as handle:
        result = list(csv.DictReader(handle))
    assert result[0]["overall_urgency"] == "ROUTINE"


def test_legacy_coordinator_rejects_nonfinite():
    from icu_multimodal.agents import ICUMultimodalCoordinator
    from icu_multimodal.models import FrontierPayload
    payload = FrontierPayload("T", "KEY", float("nan"), 0.0, "NOMINAL")
    with pytest.raises(ValueError, match="finite"):
        ICUMultimodalCoordinator().process(payload)
