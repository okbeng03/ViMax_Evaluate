# Data Model: Agent图像评估系统

## Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────────┐
│   Project   │ 1    N│  EvaluationTask  │ N    1│ EvaluationResult│
│  (项目/批次) │──────│   (评估任务)      │──────│   (评估结果)     │
└─────────────┘       └──────────────────┘       └─────────────────┘
```

## Entities

### Project (项目)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | 唯一标识符 |
| name | String(255) | NOT NULL | 项目名称 |
| description | Text | Nullable | 项目描述 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

### EvaluationTask (评估任务)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | 唯一标识符 |
| project_id | UUID | Foreign Key, Nullable | 所属项目ID |
| image_url | String(2048) | NOT NULL | 图片URL |
| image_base64 | Text | Nullable | 图片Base64编码 |
| prompt | Text | NOT NULL | 原始prompt文本 |
| status | Enum | NOT NULL, Default: pending | 任务状态 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |
| completed_at | DateTime | Nullable | 完成时间 |

**Status Values**:
- `pending`: 任务已创建，等待处理
- `queued`: 任务已进入队列
- `processing`: 任务执行中
- `completed`: 任务已完成
- `failed`: 任务失败

### EvaluationResult (评估结果)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | 唯一标识符 |
| task_id | UUID | Foreign Key, UNIQUE | 关联任务ID |
| clip_score | Float | NOT NULL | CLIP语义相似度 (0-1) |
| clip_interpretation | String | NOT NULL | 语义一致性解释 |
| structured_description | Text | NOT NULL | Qwen VL结构化描述 |
| llm_analysis | Text | NOT NULL | LLM对比分析结论 |
| llm_consistency | String | NOT NULL | 一致性判断 |
| overall_score | Float | NOT NULL | 综合评分 (0-100) |
| processing_time_ms | Integer | NOT NULL | 处理耗时(毫秒) |
| created_at | DateTime | NOT NULL | 创建时间 |

**CLIP Interpretation Values**:
- `consistent`: 语义一致 (score ≥ 0.7)
- `inconsistent`: 语义不一致 (score ≤ 0.5)
- `ambiguous`: 模糊区间 (0.5 < score < 0.7)

**LLM Consistency Values**:
- `consistent`: 内容一致
- `partially_consistent`: 部分一致
- `inconsistent`: 不一致

---

## API Models (Pydantic)

### Request Models

```python
class TaskCreateRequest(BaseModel):
    """创建评估任务请求"""
    project_id: Optional[UUID] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    prompt: str
    
    @field_validator('image_url', 'image_base64')
    @classmethod
    def at_least_one_image_source(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        # 至少提供一种图片来源
        return v

class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
```

### Response Models

```python
class TaskCreateResponse(BaseModel):
    """创建任务响应"""
    task_id: UUID
    status: TaskStatus
    created_at: datetime

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: UUID
    status: TaskStatus
    progress: Optional[ProgressInfo]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

class EvaluationResultResponse(BaseModel):
    """评估结果响应"""
    task_id: UUID
    clip_score: float
    clip_interpretation: str
    structured_description: str
    llm_analysis: str
    llm_consistency: str
    overall_score: float
    processing_time_ms: int
```

### WebSocket Message Models

```python
class WSMessage(BaseModel):
    """WebSocket消息基类"""
    type: str  # "status", "progress", "result", "error"
    task_id: UUID
    data: dict
    timestamp: datetime

class ProgressData(BaseModel):
    """进度数据"""
    current_phase: str  # "clip_evaluation", "llm_evaluation"
    phases_completed: List[str]
    phases_total: int
    progress_percent: int
```
