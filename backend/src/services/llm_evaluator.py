"""LLM evaluator using LangChain for structured comparison."""

from typing import Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.config import settings
from src.utils.logger import logger


class LLMConsistencyResult(BaseModel):
    """LLM evaluation result."""
    consistency: str = Field(description="Consistency level: consistent, partially_consistent, or inconsistent")
    analysis: str = Field(description="Detailed analysis comparing prompt and description")
    score: float = Field(description="Consistency score from 0 to 100")


class LLMEvaluator:
    """LLM-based evaluation for prompt-description consistency."""

    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize LLM client."""
        if self._initialized:
            return

        try:
            # 本地 LLM 服务可能不需要真实 API key，使用占位符
            api_key = settings.llm_api_key or "not-needed"
            
            self._llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=api_key,
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout,
            )
            self._initialized = True
            logger.info(f"LLM evaluator initialized: {settings.llm_model} @ {settings.llm_base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    async def evaluate(
        self,
        prompt: str,
        structured_description: str,
    ) -> Tuple[str, str, float]:
        """Evaluate consistency between original prompt and structured description.
        
        Returns:
            Tuple of (consistency, analysis, score)
            - consistency: "consistent", "partially_consistent", or "inconsistent"
            - analysis: Detailed analysis text
            - score: 0-100 consistency score
        """
        if not self._initialized:
            await self.initialize()

        try:
            parser = PydanticOutputParser(pydantic_object=LLMConsistencyResult)

            template = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at evaluating whether AI-generated image descriptions match the original prompts.
Analyze the structured description against the original prompt and determine:
1. Whether the main subject, actions, and attributes match
2. Whether the scene/background is appropriate
3. Whether the overall style matches
4. Provide a detailed analysis and consistency assessment"""),
                ("human", """Original Prompt: {prompt}

Structured Description: {description}

{format_instructions}""")
            ])

            chain = template | self._llm | parser

            result = await chain.ainvoke({
                "prompt": prompt,
                "description": structured_description,
                "format_instructions": parser.get_format_instructions(),
            })

            logger.info(f"LLM evaluation: consistency={result.consistency}, score={result.score}")

            return result.consistency, result.analysis, result.score

        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            raise


llm_evaluator = LLMEvaluator()
