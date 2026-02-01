"""Tests for async hallucination detection."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maven.async_hallucination_detector import AsyncHallucinationDetector
from maven.hallucination_detector import HallucinationReport


class TestAsyncHallucinationDetector:
    """Test suite for AsyncHallucinationDetector."""

    def test_init_requires_minimum_models(self):
        """Should require at least 2 models."""
        with pytest.raises(ValueError, match="At least 2 models required"):
            AsyncHallucinationDetector(models=["single_model"])

    def test_init_accepts_valid_models(self):
        """Should accept 2+ models."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.1)
        assert len(detector.model_ids) == 2

    def test_init_with_mcp_servers(self):
        """Should initialize MCP servers if provided."""
        detector = AsyncHallucinationDetector(
            models=["model1", "model2"],
            mcp_servers=[{"name": "test", "type": "http", "url": "http://localhost:8080"}],
        )
        assert detector.mcp_registry is not None

    @pytest.mark.asyncio
    async def test_detect_returns_report(self):
        """Detect should return HallucinationReport."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        # Mock the async model generation
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(
            return_value="VERDICT: RELIABLE\nISSUES: None\nCONFIDENCE: High"
        )

        with patch.object(detector, "_get_model", return_value=mock_model):
            report = await detector.detect(query="Test question", answer="Test answer")

        assert isinstance(report, HallucinationReport)
        assert report.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert 0 <= report.confidence_score <= 100

    @pytest.mark.asyncio
    async def test_detect_batch_parallel(self):
        """Batch detection should process items in parallel."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value="VERDICT: RELIABLE\nISSUES: None")

        with patch.object(detector, "_get_model", return_value=mock_model):
            items = [{"query": f"Q{i}", "answer": f"A{i}"} for i in range(5)]

            reports = await detector.detect_batch(items, max_concurrent=3)

        assert len(reports) == 5
        assert all(isinstance(r, HallucinationReport) for r in reports)

    @pytest.mark.asyncio
    async def test_detect_batch_progress_callback(self):
        """Progress callback should be called for each item."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value="VERDICT: RELIABLE")

        progress_calls = []

        def track_progress(current, total):
            progress_calls.append((current, total))

        with patch.object(detector, "_get_model", return_value=mock_model):
            items = [{"query": "Q", "answer": "A"} for _ in range(3)]
            await detector.detect_batch(items, progress_callback=track_progress)

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    @pytest.mark.asyncio
    async def test_is_hallucination_quick_check(self):
        """is_hallucination should return boolean."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value="VERDICT: UNRELIABLE\nISSUES: Fabricated")

        with patch.object(detector, "_get_model", return_value=mock_model):
            result = await detector.is_hallucination("Q", "A")

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_risk_level_critical(self):
        """Should return CRITICAL when multiple models flag unreliable."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value="VERDICT: UNRELIABLE\nISSUES: Fake")

        with patch.object(detector, "_get_model", return_value=mock_model):
            report = await detector.detect("Q", "A")

        assert report.risk_level in ["CRITICAL", "HIGH"]

    @pytest.mark.asyncio
    async def test_risk_level_low(self):
        """Should return LOW when all models agree reliable."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value="VERDICT: RELIABLE\nISSUES: None")

        with patch.object(detector, "_get_model", return_value=mock_model):
            report = await detector.detect("Q", "A")

        assert report.risk_level == "LOW"

    def test_get_trace(self):
        """Should return copy of trace."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"])
        detector._trace = [MagicMock()]

        trace = detector.get_trace()
        assert len(trace) == 1
        # Should be a copy
        trace.append(MagicMock())
        assert len(detector._trace) == 1


class TestAsyncDetectorIntegration:
    """Integration tests for async detector."""

    @pytest.mark.asyncio
    async def test_handles_model_errors(self):
        """Should handle model errors gracefully."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(side_effect=Exception("API Error"))

        with patch.object(detector, "_get_model", return_value=mock_model):
            # Should not raise, should handle error
            report = await detector.detect("Q", "A")

        assert isinstance(report, HallucinationReport)

    @pytest.mark.asyncio
    async def test_batch_handles_individual_errors(self):
        """Batch should continue on individual item errors."""
        detector = AsyncHallucinationDetector(models=["model1", "model2"], rate_limit_delay=0.01)

        call_count = [0]

        async def mock_generate(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 3 == 0:
                raise Exception("Intermittent error")
            return "VERDICT: RELIABLE"

        mock_model = AsyncMock()
        mock_model.generate = mock_generate

        with patch.object(detector, "_get_model", return_value=mock_model):
            items = [{"query": f"Q{i}", "answer": f"A{i}"} for i in range(3)]
            reports = await detector.detect_batch(items)

        assert len(reports) == 3
