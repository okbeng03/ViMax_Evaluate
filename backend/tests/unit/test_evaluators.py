"""Unit tests for evaluators."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image
from io import BytesIO


class TestCLIPEvaluator:
    """Test CLIP evaluator."""

    @pytest.mark.asyncio
    async def test_interpret_score_consistent(self):
        """Test score interpretation for consistent."""
        from src.services.clip_evaluator import CLIPEvaluator
        
        evaluator = CLIPEvaluator()
        
        assert evaluator._interpret_score(0.85) == "consistent"
        assert evaluator._interpret_score(0.7) == "consistent"
        
    @pytest.mark.asyncio
    async def test_interpret_score_inconsistent(self):
        """Test score interpretation for inconsistent."""
        from src.services.clip_evaluator import CLIPEvaluator
        
        evaluator = CLIPEvaluator()
        
        assert evaluator._interpret_score(0.3) == "inconsistent"
        assert evaluator._interpret_score(0.5) == "inconsistent"
        
    @pytest.mark.asyncio
    async def test_interpret_score_ambiguous(self):
        """Test score interpretation for ambiguous."""
        from src.services.clip_evaluator import CLIPEvaluator
        
        evaluator = CLIPEvaluator()
        
        assert evaluator._interpret_score(0.6) == "ambiguous"
        assert evaluator._interpret_score(0.55) == "ambiguous"


class TestLLMEvaluator:
    """Test LLM evaluator."""

    @pytest.mark.asyncio
    async def test_evaluate_fallback_on_error(self):
        """Test that LLM evaluator falls back gracefully on error."""
        from src.services.llm_evaluator import LLMEvaluator
        
        evaluator = LLMEvaluator()
        evaluator._initialized = True
        evaluator._llm = MagicMock()
        
        with patch.object(evaluator._llm, "ainvoke", side_effect=Exception("API Error")):
            consistency, analysis, score = await evaluator.evaluate(
                "A red apple on a table",
                "A fresh red apple resting on a wooden table"
            )
            
            assert consistency == "partially_consistent"
            assert score == 50.0


class TestEvaluationPipeline:
    """Test evaluation pipeline."""

    @pytest.mark.asyncio
    async def test_calculate_overall_score(self):
        """Test overall score calculation."""
        from src.services.evaluation_pipeline import EvaluationPipeline
        
        pipeline = EvaluationPipeline()
        
        score = pipeline._calculate_overall_score(0.8, 75.0)
        expected = (0.8 * 100 * 0.4) + (75.0 * 0.6)
        assert abs(score - expected) < 0.01
        
    @pytest.mark.asyncio
    async def test_calculate_overall_score_weights(self):
        """Test that CLIP weight is 0.4 and LLM weight is 0.6."""
        from src.services.evaluation_pipeline import EvaluationPipeline
        
        pipeline = EvaluationPipeline()
        
        score = pipeline._calculate_overall_score(100.0, 0.0)
        assert abs(score - 40.0) < 0.01
        
        score = pipeline._calculate_overall_score(0.0, 100.0)
        assert abs(score - 60.0) < 0.01
