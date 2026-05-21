"""LLM evaluator using LangChain for structured comparison."""

from typing import Tuple, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.config import settings
from src.utils.logger import logger
from src.services.llama_server import llama_server


class RequirementMatch(BaseModel):
    """单个需求的匹配情况"""
    item: str = Field(description="需求项名称")
    status: str = Field(description="匹配状态: matched, missing, incorrect")
    confidence: float = Field(description="置信度 0-1")
    evidence: str = Field(description="支持或反对的证据")


class DimensionScore(BaseModel):
    """各维度的评分"""
    subject_consistency: float = Field(description="主体一致性 0-100")
    action_consistency: float = Field(description="动作一致性 0-100")
    attribute_consistency: float = Field(description="属性一致性 0-100")
    spatial_consistency: float = Field(description="空间一致性 0-100")
    composition_consistency: float = Field(description="构图一致性 0-100")
    lighting_consistency: float = Field(description="光影一致性 0-100")
    style_consistency: float = Field(description="风格一致性 0-100")
    anatomy_quality: float = Field(description="解剖质量 0-100")
    artifact_quality: float = Field(description="生成质量 0-100")


class LLMConsistencyResult(BaseModel):
    """LLM 评估结果"""
    consistency: str = Field(description="一致性等级: consistent, partially_consistent, inconsistent")
    overall_score: float = Field(description="总体评分 0-100")
    dimension_scores: DimensionScore = Field(description="各维度评分")
    matched_requirements: List[RequirementMatch] = Field(description="匹配的需求列表")
    missing_requirements: List[RequirementMatch] = Field(description="缺失的需求列表")
    incorrect_requirements: List[RequirementMatch] = Field(description="错误的需求列表")
    extra_elements: List[str] = Field(description="图像中多余的元素")
    critical_failures: List[str] = Field(description="严重失败列表")
    analysis: str = Field(description="详细分析")


# Prompts
# 严格遵守 schema
# SYSTEM_PROMPT = \
# """
# [Role]
# 你是一个专业的 AI 图像生成质量评估专家。

# 你专门负责：
# - 评估 AI 生成图像与原始 Prompt 的一致性
# - 检测生成错误
# - 分析镜头、构图、风格、光影、主体等是否符合要求
# - 输出适用于自动化 Pipeline 的结构化评估结果

# [Task]
# 你的任务是：
# - 判断图像是否符合 Prompt
# - 识别缺失内容
# - 识别错误内容
# - 识别多余内容
# - 识别生成缺陷
# - 输出结构化评估结果

# [Input]
# 你将收到：
# 1. Original Prompt
# 用户原始图像生成提示词

# 2. Structured Description
# 由视觉模型（Qwen-VL）生成的结构化图像分析结果

# [Output]
# {format_instructions}

# [Evaluation Principles]

# 你必须重点关注：

# 1. 主体一致性
# - 人物
# - 动物
# - 物体
# - 数量
# - 性别
# - 年龄
# - 外观

# 2. 动作一致性
# - 姿势
# - 行为
# - 朝向
# - 互动关系

# 3. 空间与构图一致性
# - 左右位置
# - 前后关系
# - 遮挡关系
# - 镜头角度
# - 景别
# - 构图方式

# 4. 光影一致性
# - 光源方向
# - 光照强弱
# - 阴影方向
# - 时间氛围

# 5. 风格一致性
# - 动画风格
# - 写实风格
# - 电影感
# - 渲染风格
# - 材质表现

# 6. 文字一致性
# - 是否存在错误文字
# - 是否缺失指定文字
# - OCR 是否错误

# 7. 生成质量
# - 多余肢体
# - 畸形
# - 解剖错误
# - 透视错误
# - 漂浮物体
# - 重复元素
# - 模糊区域
# - 不合理结构

# [Critical Failure Rules]

# 以下情况属于严重错误，必须大幅扣分：

# - 主体缺失
# - 主体数量错误
# - 镜头角度错误
# - 左右方向错误
# - 动作完全错误
# - 光照方向错误
# - 汉字/文字错误
# - 关键元素缺失

# [Scoring Rules]

# 分数范围：0-100

# 评分参考：

# 90-100:
# 几乎完全符合 Prompt，仅有轻微细节偏差

# 75-89:
# 主体与核心场景正确，但存在一些细节偏差

# 50-74:
# 部分符合，但存在明显错误或缺失

# 25-49:
# 大量内容不匹配

# 0-24:
# 核心内容完全错误

# [Important Rules]

# 1. 优先关注 Prompt 中的核心要求
# 例如：
# - 镜头
# - 主体
# - 动作
# - 光照
# - 汉字
# 这些优先级高于普通背景细节

# 2. 不要因为背景小细节缺失而严重扣分

# 3. 不要 hallucinate
# 只能基于提供的信息分析

# 4. 明确区分：
# - missing（缺失）
# - incorrect（错误）
# - extra（多余）

# 5. 如果存在严重生成缺陷：
# 必须写入 critical_failures

# 6. analysis 必须具有可解释性
# 说明为什么扣分

# 7. 输出必须严格符合 schema
# """

# 尊重创意 schema
SYSTEM_PROMPT = \
"""
[Role]
你是一个专业的 AI 图像生成质量评估专家。

你的职责是：
1. 判断生成图像是否偏离原始 Prompt 的核心意图
2. 检测明显的生成缺陷与结构性错误
3. 输出适用于自动化筛选的评估结果

[Input]
你将收到：
1. Original Prompt
用户原始图像生成提示词

2. Structured Description
由视觉模型（Qwen-VL）生成的结构化图像分析结果

[Output]
{format_instructions}

[Core Evaluation Goal]

你的核心任务不是逐字比对 Prompt。

而是判断：

- 图像是否仍然符合 Prompt 的核心语义
- 是否出现明显偏题
- 是否存在严重结构错误
- 是否存在明显 AI 生成缺陷

允许：
- 合理的创造性变化
- 风格化变化
- 非关键细节变化
- 背景细节变化
- 非核心属性变化

不要因为：
- 小细节缺失
- 次要元素变化
- 风格轻微不同
而严重扣分。

[重点检查内容]

优先检查以下内容：

1. 核心主体是否正确
- 主体是否存在
- 主体类型是否正确
- 人数是否正确
- 是否出现错误主体

2. 核心动作与场景是否正确
- 主行为是否正确
- 场景是否明显偏题
- 空间关系是否严重错误

3. 是否存在明显生成缺陷
例如：
- 多余手臂
- 多余手指
- 缺失肢体
- 畸形结构
- 面部崩坏
- 错误文字
- 奇怪字符
- 漂浮物体
- 融合物体
- 重复结构

4. 是否存在严重结构性错误
例如：
- 主角消失
- 主角错误
- 动作完全错误
- 左右关系完全错误
- 镜头逻辑完全错误
- 汉字错误
- 关键元素缺失

[Scoring Philosophy]

100分不代表完全逐字匹配 Prompt。

而代表：
- 图像很好地表达了 Prompt 的核心意图
- 没有明显偏题
- 没有明显生成缺陷

评分时：
- 核心结构错误 > 细节错误
- 主体错误 > 风格错误
- 生成缺陷 > 小属性偏差
- 偏题 > 细节遗漏

[Consistency Levels]

consistent:
图像整体符合 Prompt 核心意图，没有明显结构性错误。

partially_consistent:
图像基本符合 Prompt，但存在部分错误、缺失或生成缺陷。

inconsistent:
图像已经明显偏离 Prompt，或存在严重结构问题。

[Important Rules]

1. 不要过度严格匹配细节
允许合理创造性。

2. 不要因为背景小细节而严重扣分

3. 重点关注：
- 主体
- 动作
- 场景
- 空间关系
- 生成缺陷

4. 明确区分：
- missing
- incorrect
- extra
- artifact

5. analysis 必须解释：
- 为什么认为图像没有偏题
- 或为什么认为已经偏题
- 哪些问题属于严重问题

6. 只能基于输入内容分析
不要 hallucinate

7. 输出必须严格符合 schema
"""

USER_PROMPT = \
"""
<Original_Prompt>
{prompt}
</Original_Prompt>

<Structured_Description>
{description}
</Structured_Description>
"""


EVAL_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_PROMPT),
])


class LLMEvaluator:
    """LLM-based evaluation for prompt-description consistency."""

    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize LLM client (lazy - server starts on first evaluation)."""
        if self._initialized:
            return

        try:
            api_key = settings.llm_api_key or "not-needed"
            
            # LLM client pointing to where llama server will run
            self._llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=api_key,
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout,
            )
            self._initialized = True
            logger.info(f"LLM evaluator ready (server starts on demand at {settings.llm_base_url})")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    async def _ensure_server_running(self) -> None:
        """Ensure llama server is running before evaluation."""
        if not llama_server.is_running:
            logger.info("Starting llama server on demand...")
            success = await llama_server.start(timeout=settings.llama_startup_timeout)
            if not success:
                raise RuntimeError("Failed to start llama server")

    async def _shutdown_server(self) -> None:
        """Shutdown llama server after evaluation."""
        if llama_server.is_running:
            await llama_server.stop()
            logger.info("Llama server stopped after evaluation")

    async def evaluate(
        self,
        prompt: str,
        structured_description: str,
    ) -> LLMConsistencyResult:
        """Evaluate consistency between original prompt and structured description.
        
        Server lifecycle:
        - Starts llama server if not running
        - Runs evaluation
        - Stops llama server to free GPU memory
        
        Returns:
            LLMConsistencyResult with detailed evaluation
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Ensure server is running
            await self._ensure_server_running()

            parser = PydanticOutputParser(pydantic_object=LLMConsistencyResult)
            chain = EVAL_TEMPLATE | self._llm | parser

            result = await chain.ainvoke({
                "prompt": prompt,
                "description": structured_description,
                "format_instructions": parser.get_format_instructions(),
            })

            logger.info(
                f"LLM evaluation: consistency={result.consistency}, "
                f"overall_score={result.overall_score}, "
                f"matched={len(result.matched_requirements)}, "
                f"missing={len(result.missing_requirements)}, "
                f"incorrect={len(result.incorrect_requirements)}, "
                f"critical_failures={len(result.critical_failures)}"
            )

            return result

        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            raise
        finally:
            # Always shutdown server after evaluation to free GPU memory
            await self._shutdown_server()


llm_evaluator = LLMEvaluator()
