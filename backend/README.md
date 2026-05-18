# Agent图像评估系统 - Backend

FastAPI后端服务，提供CLIP和LLM驱动的图像质量评估能力。

## 技术栈

- **Python 3.13**
- **FastAPI** - Web框架
- **SQLAlchemy** + **aiosqlite** - 异步数据库ORM
- **open_clip_torch** - CLIP模型加载与推理
- **LangChain** - LLM调用与Chain构建
- **WebSocket** - 实时进度推送

## 项目结构

```
backend/
├── src/
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # Pydantic模型
│   ├── services/            # 业务逻辑
│   │   ├── clip_evaluator.py # CLIP评估服务
│   │   ├── llm_evaluator.py # LLM评估服务
│   │   ├── comfyui_client.py # ComfyUI客户端
│   │   ├── task_manager.py  # 任务管理器
│   │   ├── task_queue.py    # 异步任务队列
│   │   └── websocket_manager.py # WebSocket管理
│   ├── routers/             # API路由
│   │   ├── tasks.py         # 任务API
│   │   ├── projects.py      # 项目API
│   │   └── websocket.py     # WebSocket端点
│   ├── db/                  # 数据库
│   └── utils/               # 工具函数
└── tests/                   # 测试
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 数据库
DATABASE_URL=sqlite+aiosqlite:///data/evaluations.db

# ComfyUI
COMFYUI_URL=http://localhost:8188

# LLM
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# CLIP
CLIP_DEVICE=cuda
```

### 3. 启动服务

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 任务管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/tasks` | 创建评估任务 |
| GET | `/api/v1/tasks/{task_id}` | 获取任务状态 |
| GET | `/api/v1/tasks/{task_id}/result` | 获取评估结果 |
| GET | `/api/v1/tasks` | 批量查询任务 |

### 项目管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects/{project_id}` | 获取项目详情 |
| GET | `/api/v1/projects` | 批量查询项目 |

### WebSocket

| 端点 | 描述 |
|------|------|
| `/ws/{task_id}` | 实时任务状态推送 |

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式

```bash
ruff check .
black .
```

## License

MIT
