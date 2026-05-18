# Agent图像评估系统 - 后端

## 技术栈

- Python 3.13
- FastAPI
- SQLAlchemy + aiosqlite
- open_clip_torch (CLIP模型)
- LangChain (LLM调用)

## 项目结构

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI应用入口
│   ├── config.py         # 配置管理
│   ├── models/            # Pydantic模型
│   ├── services/          # 业务逻辑
│   ├── routers/           # API路由
│   ├── db/                # 数据库
│   └── utils/             # 工具函数
├── tests/
│   ├── unit/              # 单元测试
│   ├── contract/          # 契约测试
│   └── integration/       # 集成测试
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行服务

```bash
uvicorn src.main:app --reload --port 8000
```

### 4. API文档

访问 http://localhost:8000/docs 查看交互式API文档。

## 环境变量

创建 `.env` 文件：

```env
DATABASE_URL=sqlite+aiosqlite:///data/evaluations.db
COMFYUI_URL=http://localhost:8188
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LOG_LEVEL=INFO
```

## 测试

```bash
# 运行所有测试
pytest

# 运行契约测试
pytest tests/contract/

# 运行集成测试
pytest tests/integration/

# 带覆盖率报告
pytest --cov=src --cov-report=html
```
