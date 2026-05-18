# Implementation Plan: Agent图像评估系统

**Branch**: `main` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-agent-image-evaluation/spec.md`

## Summary

构建一个提供Agent图像评估能力的全栈应用。核心功能包括：
1. **CLIP语义一致性评估**：使用open_clip_torch加载apple/DFN2B-CLIP-ViT-L-14-39B模型评估图片与prompt的语义相似度
2. **LLM结构化对比评估**：通过ComfyUI Qwen VL工作流生成图片结构化描述，再使用LangChain调用LLM与原始prompt对比分析
3. **异步任务系统**：采用ComfyUI风格的API模式（提交任务→返回任务ID→WebSocket追踪进度）
4. **前端展示**：React + Ant Design构建的历史评估结果查看页面

技术栈：Python FastAPI (后端) | React + Ant Design (前端) | SQLite (数据库)

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**:
- FastAPI: Web框架
- open_clip_torch: CLIP模型加载与推理
- requests: 调用ComfyUI Qwen VL工作流API
- langchain: LLM调用与Chain构建
- SQLAlchemy + aiosqlite: 异步数据库ORM
- WebSocket (FastAPI原生): 实时进度推送
- React 18 + Ant Design 6: 前端UI框架

**Storage**: SQLite (本地文件数据库)

**Testing**: pytest + pytest-asyncio (后端), Jest + React Testing Library (前端)

**Target Platform**: Linux/macOS (后端API服务), 浏览器 (前端)

**Project Type**: Web服务 + 前端应用

**Performance Goals**:
- 任务提交响应: <5秒
- 单张图片评估: <60秒
- WebSocket推送延迟: <1秒

**Constraints**:
- CLIP模型需GPU加速（CUDA）
- ComfyUI Qwen VL工作流需独立部署
- LLM服务需外部API或本地部署

**Scale/Scope**:
- 并发评估任务: 10+
- 历史记录: 1000+条支持分页

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 检查项 | 状态 |
|------|--------|------|
| I. 代码质量 | 函数<50行，命名规范，文档注释，配置外部化 | ✅ PASS |
| II. 测试标准 | 单元测试、API契约测试、集成测试规划 | ✅ PASS |
| III. UX一致性 | Ant Design统一组件库，响应式设计 | ✅ PASS |
| IV. 性能要求 | API响应<200ms，评估<60秒，WebSocket<1秒 | ✅ PASS |
| V. 技术债务 | 模块化设计，易于替换组件 | ✅ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-agent-image-evaluation/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output
│   └── api-contracts.md
└── tasks.md              # Phase 2 output (/speckit.tasks)
```

### Source Code

```text
vimax_evaluate/
├── backend/                    # FastAPI后端
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI应用入口
│   │   ├── config.py           # 配置管理
│   │   ├── models/              # Pydantic模型
│   │   │   ├── __init__.py
│   │   │   ├── task.py          # 评估任务模型
│   │   │   ├── result.py        # 评估结果模型
│   │   │   └── project.py      # 项目模型
│   │   ├── services/            # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── clip_evaluator.py    # CLIP评估服务
│   │   │   ├── llm_evaluator.py     # LLM评估服务
│   │   │   └── task_manager.py       # 任务管理器
│   │   ├── routers/             # API路由
│   │   │   ├── __init__.py
│   │   │   ├── tasks.py         # 任务API
│   │   │   ├── projects.py      # 项目API
│   │   │   └── websocket.py     # WebSocket端点
│   │   ├── db/                  # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # 数据库连接
│   │   │   └── models.py        # SQLAlchemy模型
│   │   └── utils/               # 工具函数
│   │       ├── __init__.py
│   │       └── logger.py        # 日志工具
│   ├── tests/
│   │   ├── unit/
│   │   ├── contract/
│   │   └── integration/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # React前端
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api/                # API调用
│   │   │   ├── client.ts        # HTTP客户端
│   │   │   └── websocket.ts    # WebSocket客户端
│   │   ├── pages/
│   │   │   ├── TaskSubmitPage.tsx   # 任务提交页
│   │   │   ├── HistoryListPage.tsx  # 历史记录列表
│   │   │   └── EvaluationDetailPage.tsx  # 评估详情
│   │   ├── components/         # 通用组件
│   │   └── types/              # TypeScript类型
│   ├── package.json
│   └── README.md
│
└── data/                       # 数据目录
    └── evaluations.db          # SQLite数据库
```

**Structure Decision**: 采用前后端分离架构，backend提供REST API + WebSocket，frontend为独立SPA应用。数据存储使用本地SQLite文件。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| LangChain依赖 | 标准化LLM调用，提供Chain能力便于prompt管理 | 直接调用API可减少依赖但缺少LangChain的调试和扩展能力 |
