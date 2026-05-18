# Quickstart: Agent图像评估系统

## 环境要求

- Python 3.13
- Node.js 18+
- CUDA 11.8+ (GPU加速，可选)
- ComfyUI (Qwen VL工作流，需独立部署)

## 后端安装

### 1. 克隆并安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# ComfyUI API 配置
COMFYUI_API_URL=http://localhost:8188

# LLM 配置 (根据实际LLM服务填写)
LLM_PROVIDER=openai  # 或 "local", "anthropic"
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///../data/evaluations.db

# 应用配置
LOG_LEVEL=INFO
```

### 3. 初始化数据库

```bash
python -m src.db.init_db
```

### 4. 启动后端服务

```bash
# 开发模式
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

## 前端安装

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 访问应用

打开浏览器访问 `http://localhost:5173`

## 快速使用

### 方式一：使用前端界面

1. 打开前端页面
2. 选择或创建项目
3. 输入图片URL和prompt
4. 提交评估任务
5. 实时查看评估进度
6. 查看评估结果

### 方式二：使用API

```bash
# 1. 创建评估任务
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/generated_image.png",
    "prompt": "一只橘色的猫坐在窗台上"
  }'

# 返回: {"task_id": "...", "status": "pending", "created_at": "..."}

# 2. 查询任务状态
curl http://localhost:8000/api/v1/tasks/{task_id}

# 3. 获取评估结果
curl http://localhost:8000/api/v1/tasks/{task_id}/result

# 4. WebSocket实时追踪
# 使用wscat连接
wscat -c ws://localhost:8000/ws/{task_id}
```

## 测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行契约测试
pytest tests/contract/

# 生成覆盖率报告
pytest --cov=src tests/
```

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并生成覆盖率
npm test -- --coverage
```

## 常见问题

### Q: CLIP模型加载失败
A: 确保网络连接正常，首次运行会自动下载模型。可预先下载模型到本地缓存目录。

### Q: ComfyUI连接失败
A: 确保ComfyUI服务已启动，Qwen VL工作流已正确配置。检查`COMFYUI_API_URL`配置。

### Q: LLM调用超时
A: 检查LLM服务是否可用，增加超时配置或使用本地LLM服务。

### Q: SQLite数据库锁定
A: SQLite不支持高并发写入，如需高并发请考虑迁移到PostgreSQL。
