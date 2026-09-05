"""
Tests for Prometheus metrics and enrichment engines.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.metrics import SystemMetricsCollector
from enrichment import (
    FeaturesEngine,
    IcuMultimodalEarlyWarningEngine,
    IcumultimodalearlywarningagentEnrichmentSuite,
)


class TestSystemMetricsCollector:
    """Test Prometheus metrics collection."""

    def test_initial_state(self):
        collector = SystemMetricsCollector()
        assert collector.tasks_total == 0
        assert collector.critical_alerts_total == 0
        assert collector.elevated_alerts_total == 0
        assert collector.routine_tasks_total == 0

    def test_record_critical_task(self):
        collector = SystemMetricsCollector()
        collector.record_task("CRITICAL_STAT_PANIC", 0.5)
        assert collector.tasks_total == 1
        assert collector.critical_alerts_total == 1
        assert collector.elevated_alerts_total == 0
        assert collector.routine_tasks_total == 0

    def test_record_elevated_task(self):
        collector = SystemMetricsCollector()
        collector.record_task("ELEVATED_RISK", 0.3)
        assert collector.tasks_total == 1
        assert collector.elevated_alerts_total == 1
        assert collector.critical_alerts_total == 0

    def test_record_routine_task(self):
        collector = SystemMetricsCollector()
        collector.record_task("ROUTINE", 0.1)
        assert collector.tasks_total == 1
        assert collector.routine_tasks_total == 1
        assert collector.critical_alerts_total == 0
        assert collector.elevated_alerts_total == 0

    def test_record_phi_block(self):
        collector = SystemMetricsCollector()
        collector.record_phi_block()
        collector.record_phi_block()
        assert collector.phi_blocks_total == 2

    def test_prometheus_export(self):
        collector = SystemMetricsCollector()
        collector.record_task("CRITICAL_STAT_PANIC", 0.5)
        collector.record_task("ELEVATED_RISK", 0.3)
        collector.record_phi_block()

        output = collector.export_prometheus_text()
        assert "system_tasks_total" in output
        assert "alerts_triggered_total" in output
        assert "phi_outbound_blocks_total" in output
        assert "audit_chain_blocks_total" in output
        assert "task_processing_duration_avg_seconds" in output


class TestFeaturesEngine:
    """Test the FeaturesEngine enrichment module."""

    def test_optimal_status(self):
        engine = FeaturesEngine(threshold=1.0)
        result = engine.evaluate(0.5, 0.2)
        assert result.status == "OPTIMAL"
        assert len(result.alerts) == 0

    def test_warning_status(self):
        engine = FeaturesEngine(threshold=1.0)
        result = engine.evaluate(1.5, 0.5)
        assert result.status == "WARNING"
        assert len(result.alerts) == 1

    def test_critical_status(self):
        engine = FeaturesEngine(threshold=1.0)
        result = engine.evaluate(5.0, 1.0)
        assert result.status == "CRITICAL_ALERT"
        assert len(result.alerts) == 1

    def test_history_tracking(self):
        engine = FeaturesEngine(threshold=1.0)
        engine.evaluate(0.5, 0.2)
        engine.evaluate(1.5, 0.5)
        assert len(engine.history) == 2


class TestIcuMultimodalEarlyWarningEngine:
    """Test the ICU Multimodal Early Warning Engine."""

    def test_optimal_evaluation(self):
        engine = IcuMultimodalEarlyWarningEngine(threshold=1.0)
        result = engine.evaluate(0.5, 0.2)
        assert result.status == "OPTIMAL"
        assert result.feature_name == "ICU Multimodal Early Warning"

    def test_warning_evaluation(self):
        engine = IcuMultimodalEarlyWarningEngine(threshold=1.0)
        result = engine.evaluate(1.5, 0.5)
        assert result.status == "WARNING"

    def test_critical_evaluation(self):
        engine = IcuMultimodalEarlyWarningEngine(threshold=1.0)
        result = engine.evaluate(5.0, 1.0)
        assert result.status == "CRITICAL_ALERT"


class TestEnrichmentSuite:
    """Test the composite enrichment suite."""

    def test_execute_all(self):
        suite = IcumultimodalearlywarningagentEnrichmentSuite()
        results = suite.execute_all(primary_val=0.5, secondary_val=0.2)
        assert len(results) == 8
        for key, result in results.items():
            assert result.status in ["OPTIMAL", "WARNING", "CRITICAL_ALERT"]
            assert isinstance(result.recommendations, list)

    def test_threshold_escalation(self):
        suite = IcumultimodalearlywarningagentEnrichmentSuite()
        results = suite.execute_all(primary_val=10.0, secondary_val=5.0)
        for key, result in results.items():
            assert result.status in ["WARNING", "CRITICAL_ALERT"]
            assert len(result.alerts) > 0
