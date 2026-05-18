# Research: Agent图像评估系统

## 1. CLIP模型评估方案

**Decision**: 使用open_clip_torch加载apple/DFN2B-CLIP-ViT-L-14-39B模型

**Rationale**:
- open_clip_torch是OpenCLIP的PyTorch实现，官方维护，支持苹果DFN2B模型
- 模型可从HuggingFace或本地缓存加载
- 支持GPU加速，评估效率高

**Alternatives considered**:
- transformers CLIP: 功能类似但open_clip对苹果模型支持更好
- 本地部署CLIP: 需要更多存储空间

**Implementation notes**:
```python
import open_clip
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-L-14-39B",
    pretrained="dfn2b"
)
```

---

## 2. ComfyUI Qwen VL工作流调用

**Decision**: 使用requests库调用ComfyUI工作流API

**Rationale**:
- ComfyUI提供标准HTTP API接口
- requests库轻量、成熟
- 工作流可通过API触发并获取结果

**API模式**:
- POST /api/prompt - 提交工作流
- GET /api/history/{prompt_id} - 获取结果
- WebSocket /api/ws - 实时进度

**Alternatives considered**:
- 直接集成Qwen VL模型: 复杂度高，不利用现有ComfyUI工作流
- SDK调用: ComfyUI无官方SDK

---

## 3. LangChain LLM评估

**Decision**: 使用LangChain调用LLM进行prompt对比分析

**Rationale**:
- LangChain提供标准化的LLM调用接口
- 支持多种LLM后端（OpenAI、本地模型等）
- Prompt模板管理方便

**Chain设计**:
```
Image Description (from Qwen VL) + Original Prompt → LLM → Analysis Result
```

**Alternatives considered**:
- 直接API调用: 缺少LangChain的prompt管理和调试能力
- 其他框架 (LlamaIndex): LangChain更通用

---

## 4. 异步任务系统设计

**Decision**: 任务队列 + WebSocket实时推送

**Rationale**:
- FastAPI原生支持async/await
- asyncio.Queue适合轻量任务队列
- WebSocket与FastAPI无缝集成
- 符合ComfyUI API设计风格

**任务状态机**:
```
pending → queued → processing (clip_evaluation) → processing (llm_evaluation) → completed
                ↓                              ↓
             failed                          failed
```

---

## 5. SQLite数据库设计

**Decision**: SQLAlchemy + aiosqlite异步访问

**Rationale**:
- aiosqlite提供异步数据库访问，与FastAPI异步特性匹配
- SQLite适合单实例部署，开发测试方便
- 数据量可控（1000+记录）

**替代方案考虑**:
- PostgreSQL: 需要额外服务，复杂度高
- MongoDB: 不适合结构化评估数据

---

## 6. 前端技术选型

**Decision**: React 18 + Ant Design 6 + Vite

**Rationale**:
- Ant Design 6是最新的企业级UI组件库，包含性能优化和新特性
- Vite提供快速开发体验
- TypeScript提供类型安全
- 与章程III. UX一致性原则一致

**状态管理**:
- React Query: 服务端状态
- Zustand: 客户端UI状态
