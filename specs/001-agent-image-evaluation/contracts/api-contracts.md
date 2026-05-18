# API Contracts: Agent图像评估系统

## REST API

### Base URL
```
http://localhost:8000/api/v1
```

### Content-Type
所有请求和响应均为JSON格式：`application/json`

---

## 任务管理 API

### 创建评估任务

**Endpoint**: `POST /tasks`

**Request Body**:
```json
{
  "project_id": "uuid-string (optional)",
  "image_url": "string (optional, image URL)",
  "image_base64": "string (optional, base64 encoded image)",
  "prompt": "string (required)"
}
```

**Response** (201 Created):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-05-18T15:00:00Z"
}
```

**Error Responses**:
- 400 Bad Request: 缺少图片或prompt
- 422 Unprocessable Entity: 图片格式不支持

---

### 查询任务状态

**Endpoint**: `GET /tasks/{task_id}`

**Response** (200 OK):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "project_id": "uuid-string or null",
  "created_at": "2026-05-18T15:00:00Z",
  "updated_at": "2026-05-18T15:01:30Z",
  "completed_at": "2026-05-18T15:01:30Z"
}
```

---

### 获取评估结果

**Endpoint**: `GET /tasks/{task_id}/result`

**Response** (200 OK):
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "clip_score": 0.85,
  "clip_interpretation": "consistent",
  "structured_description": "一只橘色的猫坐在窗台上...",
  "llm_analysis": "图片内容与prompt描述高度一致...",
  "llm_consistency": "consistent",
  "overall_score": 82,
  "processing_time_ms": 45230
}
```

**Error Responses**:
- 404 Not Found: 任务不存在
- 202 Accepted: 任务尚未完成（返回当前状态）

---

### 批量查询任务

**Endpoint**: `GET /tasks`

**Query Parameters**:
- `project_id`: UUID (optional) - 按项目筛选
- `status`: string (optional) - 按状态筛选
- `limit`: integer (default: 20, max: 100)
- `offset`: integer (default: 0)
- `start_date`: ISO date (optional)
- `end_date`: ISO date (optional)

**Response** (200 OK):
```json
{
  "tasks": [
    {
      "task_id": "uuid",
      "status": "completed",
      "prompt_summary": "一只橘色的猫...",
      "overall_score": 82,
      "created_at": "2026-05-18T15:00:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

---

## 项目管理 API

### 创建项目

**Endpoint**: `POST /projects`

**Request Body**:
```json
{
  "name": "Image Generation Test",
  "description": "AI图片生成质量评估项目"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Image Generation Test",
  "description": "AI图片生成质量评估项目",
  "created_at": "2026-05-18T15:00:00Z",
  "updated_at": "2026-05-18T15:00:00Z"
}
```

---

### 获取项目列表

**Endpoint**: `GET /projects`

**Query Parameters**:
- `limit`: integer (default: 20)
- `offset`: integer (default: 0)

**Response** (200 OK):
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Image Generation Test",
      "description": "...",
      "task_count": 45,
      "created_at": "2026-05-18T15:00:00Z"
    }
  ],
  "total": 10
}
```

---

### 获取项目详情

**Endpoint**: `GET /projects/{project_id}`

**Response** (200 OK):
```json
{
  "id": "uuid",
  "name": "Image Generation Test",
  "description": "...",
  "task_count": 45,
  "avg_score": 78.5,
  "created_at": "2026-05-18T15:00:00Z",
  "updated_at": "2026-05-18T15:00:00Z"
}
```

---

## WebSocket API

### 连接端点

**Endpoint**: `ws://localhost:8000/ws/{task_id}`

### 连接流程

1. 建立WebSocket连接
2. 服务器立即推送当前任务状态
3. 接收任务进度更新
4. 任务完成后接收最终结果
5. 连接可主动关闭

### 消息格式

**服务端推送 - 状态更新**:
```json
{
  "type": "status",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "status": "processing",
    "progress": {
      "current_phase": "llm_evaluation",
      "phases_completed": ["clip_evaluation"],
      "phases_total": 2,
      "progress_percent": 50
    }
  },
  "timestamp": "2026-05-18T15:00:30Z"
}
```

**服务端推送 - 结果**:
```json
{
  "type": "result",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "clip_score": 0.85,
    "clip_interpretation": "consistent",
    "overall_score": 82,
    "llm_consistency": "consistent"
  },
  "timestamp": "2026-05-18T15:01:30Z"
}
```

**服务端推送 - 错误**:
```json
{
  "type": "error",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "error_type": "image_load_failed",
    "message": "无法加载图片，请检查URL是否可访问"
  },
  "timestamp": "2026-05-18T15:00:15Z"
}
```

---

## 错误响应格式

```json
{
  "error": {
    "code": "IMAGE_FORMAT_UNSUPPORTED",
    "message": "不支持的图片格式，支持的格式：PNG, JPG, JPEG, WebP",
    "details": {
      "received_format": "gif"
    }
  }
}
```

### 错误码列表

| Code | HTTP Status | Description |
|------|-------------|-------------|
| MISSING_REQUIRED_FIELD | 400 | 缺少必填字段 |
| IMAGE_FORMAT_UNSUPPORTED | 422 | 图片格式不支持 |
| TASK_NOT_FOUND | 404 | 任务不存在 |
| PROJECT_NOT_FOUND | 404 | 项目不存在 |
| TASK_NOT_COMPLETED | 202 | 任务尚未完成 |
| INTERNAL_ERROR | 500 | 内部错误 |
