"""
Security-focused tests for ICU Multimodal Early Warning Agent.
Tests PHI guard, audit trail, and secret management.
"""
import os
import sys
from pathlib import Path

# Set required environment variable before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-unit-tests-only-do-not-use-in-production")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import (
    AuditLogger,
    AuditTrail,
    PHIGuard,
    SecurityException,
    assert_no_phi,
)


class TestPHIGuard:
    """Test PHI detection and redaction."""

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_dob_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_patient_name_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_john_doe_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient John Doe admitted")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task TASK-2026-001 processed successfully")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")

    def test_none_text_passes(self):
        PHIGuard.assert_no_phi(None)

    def test_phi_redaction(self):
        text = "Patient MRN-12345678 has SSN 123-45-6789"
        redacted = PHIGuard.redact_phi(text)
        assert "MRN-12345678" not in redacted
        assert "123-45-6789" not in redacted
        assert "[REDACTED_IDENTIFIER]" in redacted

    def test_redaction_preserves_safe_text(self):
        text = "System status: OPTIMAL. Task completed successfully."
        redacted = PHIGuard.redact_phi(text)
        assert redacted == text


class TestAuditTrail:
    """Test HMAC-SHA256 audit trail integrity."""

    def test_audit_trail_requires_secret_key(self):
        """AuditTrail should raise exception if no key provided."""
        original_key = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(SecurityException):
                AuditTrail()
        finally:
            if original_key:
                os.environ["AUDIT_SECRET_KEY"] = original_key

    def test_audit_trail_with_explicit_key(self):
        trail = AuditTrail(secret_key="test-key")
        assert len(trail.get_trail()) == 0

    def test_audit_trail_logging(self):
        trail = AuditTrail(secret_key="test-key")
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"key": "value"})
        assert entry["audit_id"].startswith("AUDIT-")
        assert entry["actor"] == "test_actor"
        assert entry["event_type"] == "TEST_EVENT"
        assert entry["current_hash"] != ""
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_audit_trail_chain_integrity(self):
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT1", {"data": 1})
        trail.log("actor2", "tier2", "EVENT2", {"data": 2})
        trail.log("actor3", "tier3", "EVENT3", {"data": 3})

        assert trail.verify_integrity() is True
        assert len(trail.get_trail()) == 3

    def test_audit_trail_chain_linking(self):
        trail = AuditTrail(secret_key="test-key")
        entry1 = trail.log("actor1", "tier1", "EVENT1", {"data": 1})
        entry2 = trail.log("actor2", "tier2", "EVENT2", {"data": 2})

        assert entry2["prev_hash"] == entry1["current_hash"]

    def test_audit_trail_phi_blocking(self):
        trail = AuditTrail(secret_key="test-key")
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"patient": "MRN-12345678"})


class TestAuditLogger:
    """Test global AuditLogger singleton."""

    def test_global_audit_logging(self):
        entry = AuditLogger.log("test_actor", "test_tier", "TEST_EVENT", {"status": "ok"})
        assert entry["actor"] == "test_actor"
        assert entry["event_type"] == "TEST_EVENT"

    def test_global_trail_retrieval(self):
        trail = AuditLogger.get_trail()
        assert isinstance(trail, list)

    def test_global_integrity_verification(self):
        result = AuditLogger.verify_integrity()
        assert isinstance(result, bool)
