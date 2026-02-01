"""Tests for LangChain and LlamaIndex integrations."""

import pytest
from unittest.mock import MagicMock, patch

from maven.integrations import (
    # LangChain
    MAVENCallbackHandler,
    MAVENChain,
    MAVENRetriever,
    # LlamaIndex
    MAVENQueryEngine,
    MAVENResponseEvaluator,
    MAVENResponse,
    # Common
    HallucinationCheckResult,
    HallucinationError,
    # Factory functions
    create_langchain_callback,
    wrap_langchain_chain,
    wrap_llamaindex_engine,
)
from maven.hallucination_detector import HallucinationReport


class TestHallucinationCheckResult:
    """Test HallucinationCheckResult dataclass."""

    def test_bool_true_when_not_hallucination(self):
        """Should return True when NOT a hallucination."""
        result = HallucinationCheckResult(
            is_hallucination=False,
            risk_level="LOW",
            confidence_score=95.0,
            flags=[],
            original_output="test",
        )
        assert bool(result) is True

    def test_bool_false_when_hallucination(self):
        """Should return False when IS a hallucination."""
        result = HallucinationCheckResult(
            is_hallucination=True,
            risk_level="HIGH",
            confidence_score=30.0,
            flags=["Fabricated"],
            original_output="test",
        )
        assert bool(result) is False


class TestMAVENCallbackHandler:
    """Test LangChain callback handler."""

    def test_init_creates_detector(self):
        """Should create detector with models."""
        handler = MAVENCallbackHandler(models=["m1", "m2"])
        assert handler.detector is not None
        assert handler.risk_threshold == ["CRITICAL", "HIGH"]

    def test_init_custom_threshold(self):
        """Should accept custom risk threshold."""
        handler = MAVENCallbackHandler(
            models=["m1", "m2"],
            risk_threshold=["CRITICAL"]
        )
        assert handler.risk_threshold == ["CRITICAL"]

    def test_on_llm_start_captures_prompt(self):
        """Should capture input prompt."""
        handler = MAVENCallbackHandler(models=["m1", "m2"])
        handler.on_llm_start({}, ["Test prompt"])
        assert handler._pending_input == "Test prompt"

    def test_on_llm_end_runs_detection(self):
        """Should run detection on LLM output."""
        handler = MAVENCallbackHandler(models=["m1", "m2"])
        handler._pending_input = "Test question"
        
        # Mock the detector
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(handler.detector, 'detect', return_value=mock_report):
            mock_response = MagicMock()
            mock_response.generations = [[MagicMock(text="Test output")]]
            handler.on_llm_end(mock_response)
        
        assert handler.last_detection is not None
        assert handler.last_detection.is_hallucination is False

    def test_auto_block_raises_on_hallucination(self):
        """Should raise when auto_block is True and hallucination detected."""
        handler = MAVENCallbackHandler(
            models=["m1", "m2"],
            auto_block=True
        )
        handler._pending_input = "Test"
        
        mock_report = MagicMock()
        mock_report.risk_level = "CRITICAL"
        mock_report.confidence_score = 20.0
        mock_report.flags = ["Fabricated"]
        
        with patch.object(handler.detector, 'detect', return_value=mock_report):
            mock_response = MagicMock()
            mock_response.generations = [[MagicMock(text="Fake output")]]
            
            with pytest.raises(HallucinationError):
                handler.on_llm_end(mock_response)

    def test_get_last_report(self):
        """Should return last report."""
        handler = MAVENCallbackHandler(models=["m1", "m2"])
        assert handler.get_last_report() is None
        
        handler.last_detection = HallucinationCheckResult(
            is_hallucination=False,
            risk_level="LOW",
            confidence_score=95.0,
            flags=[],
            original_output="test",
            report=MagicMock()
        )
        assert handler.get_last_report() is not None


class TestMAVENChain:
    """Test LangChain chain wrapper."""

    def test_invoke_adds_safety_metadata(self):
        """Should add safety metadata to output."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"output": "Test output"}
        
        chain = MAVENChain(chain=mock_chain, models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(chain.detector, 'detect', return_value=mock_report):
            result = chain.invoke({"input": "Test question"})
        
        assert "output" in result
        assert "is_safe" in result
        assert "risk_level" in result
        assert result["is_safe"] is True
        assert result["risk_level"] == "LOW"

    def test_invoke_flags_unsafe(self):
        """Should flag unsafe outputs."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"output": "Fake output"}
        
        chain = MAVENChain(chain=mock_chain, models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "CRITICAL"
        mock_report.confidence_score = 20.0
        mock_report.flags = ["Fabricated"]
        
        with patch.object(chain.detector, 'detect', return_value=mock_report):
            result = chain.invoke({"input": "Test"})
        
        assert result["is_safe"] is False
        assert result["risk_level"] == "CRITICAL"

    def test_include_report_option(self):
        """Should include full report when requested."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"output": "Test"}
        
        chain = MAVENChain(
            chain=mock_chain,
            models=["m1", "m2"],
            include_report=True
        )
        
        mock_report = MagicMock(spec=HallucinationReport)
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(chain.detector, 'detect', return_value=mock_report):
            result = chain.invoke({"input": "Test"})
        
        assert "report" in result

    def test_callable_alias(self):
        """__call__ should work like invoke."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"output": "Test"}
        
        chain = MAVENChain(chain=mock_chain, models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(chain.detector, 'detect', return_value=mock_report):
            result = chain({"input": "Test"})
        
        assert "is_safe" in result


class TestMAVENRetriever:
    """Test retriever wrapper."""

    def test_get_relevant_documents_adds_metadata(self):
        """Should add verification metadata to documents."""
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {}
        mock_retriever.get_relevant_documents.return_value = [mock_doc]
        
        retriever = MAVENRetriever(retriever=mock_retriever, models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(retriever.detector, 'detect', return_value=mock_report):
            docs = retriever.get_relevant_documents("Test query")
        
        assert len(docs) == 1
        assert docs[0].metadata['maven_risk_level'] == "LOW"

    def test_skip_content_check(self):
        """Should skip content check when disabled."""
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_retriever.get_relevant_documents.return_value = [mock_doc]
        
        retriever = MAVENRetriever(
            retriever=mock_retriever,
            models=["m1", "m2"],
            check_content=False
        )
        
        # Detector should not be called
        with patch.object(retriever.detector, 'detect') as mock_detect:
            docs = retriever.get_relevant_documents("Test")
            mock_detect.assert_not_called()


class TestMAVENQueryEngine:
    """Test LlamaIndex query engine wrapper."""

    def test_query_returns_maven_response(self):
        """Should return MAVENResponse with verification."""
        mock_engine = MagicMock()
        mock_engine.query.return_value = "Test answer"
        
        engine = MAVENQueryEngine(query_engine=mock_engine, models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(engine.detector, 'detect', return_value=mock_report):
            response = engine.query("Test question")
        
        assert isinstance(response, MAVENResponse)
        assert response.is_verified is True
        assert str(response) == "Test answer"

    def test_block_on_hallucination(self):
        """Should raise when block_on_hallucination is True."""
        mock_engine = MagicMock()
        mock_engine.query.return_value = "Fake answer"
        
        engine = MAVENQueryEngine(
            query_engine=mock_engine,
            models=["m1", "m2"],
            block_on_hallucination=True
        )
        
        mock_report = MagicMock()
        mock_report.risk_level = "CRITICAL"
        mock_report.confidence_score = 20.0
        mock_report.flags = ["Fabricated"]
        
        with patch.object(engine.detector, 'detect', return_value=mock_report):
            with pytest.raises(HallucinationError):
                engine.query("Test")


class TestMAVENResponse:
    """Test MAVENResponse dataclass."""

    def test_str_returns_response(self):
        """__str__ should return response text."""
        response = MAVENResponse(
            response="Test answer",
            source_response=None,
            is_verified=True,
            risk_level="LOW",
            confidence_score=95.0,
            flags=[],
        )
        assert str(response) == "Test answer"

    def test_bool_true_when_verified(self):
        """Should return True when verified."""
        response = MAVENResponse(
            response="Test",
            source_response=None,
            is_verified=True,
            risk_level="LOW",
            confidence_score=95.0,
            flags=[],
        )
        assert bool(response) is True

    def test_bool_false_when_not_verified(self):
        """Should return False when not verified."""
        response = MAVENResponse(
            response="Test",
            source_response=None,
            is_verified=False,
            risk_level="HIGH",
            confidence_score=30.0,
            flags=["Suspicious"],
        )
        assert bool(response) is False


class TestMAVENResponseEvaluator:
    """Test LlamaIndex response evaluator."""

    def test_evaluate_returns_check_result(self):
        """Should return HallucinationCheckResult."""
        evaluator = MAVENResponseEvaluator(models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(evaluator.detector, 'detect', return_value=mock_report):
            result = evaluator.evaluate("Question", "Answer")
        
        assert isinstance(result, HallucinationCheckResult)
        assert result.is_hallucination is False

    def test_evaluate_batch(self):
        """Should evaluate multiple items."""
        evaluator = MAVENResponseEvaluator(models=["m1", "m2"])
        
        mock_report = MagicMock()
        mock_report.risk_level = "LOW"
        mock_report.confidence_score = 95.0
        mock_report.flags = []
        
        with patch.object(evaluator.detector, 'detect', return_value=mock_report):
            results = evaluator.evaluate_batch([
                {"query": "Q1", "response": "R1"},
                {"query": "Q2", "response": "R2"},
            ])
        
        assert len(results) == 2


class TestFactoryFunctions:
    """Test convenience factory functions."""

    def test_create_langchain_callback(self):
        """Should create callback handler."""
        handler = create_langchain_callback(models=["m1", "m2"])
        assert isinstance(handler, MAVENCallbackHandler)

    def test_wrap_langchain_chain(self):
        """Should wrap chain."""
        mock_chain = MagicMock()
        chain = wrap_langchain_chain(chain=mock_chain, models=["m1", "m2"])
        assert isinstance(chain, MAVENChain)

    def test_wrap_llamaindex_engine(self):
        """Should wrap query engine."""
        mock_engine = MagicMock()
        engine = wrap_llamaindex_engine(query_engine=mock_engine, models=["m1", "m2"])
        assert isinstance(engine, MAVENQueryEngine)
