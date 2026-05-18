# Agent图像评估系统 - Frontend

React + Ant Design前端应用，提供图像评估任务提交和结果查看功能。

## 技术栈

- **React 18** - UI框架
- **Ant Design 6** - 组件库
- **React Router 6** - 路由管理
- **Axios** - HTTP客户端
- **Vite** - 构建工具
- **TypeScript** - 类型系统

## 项目结构

```
frontend/
├── src/
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   ├── api/                # API调用
│   │   ├── client.ts       # REST API客户端
│   │   └── websocket.ts    # WebSocket客户端
│   ├── pages/              # 页面组件
│   │   ├── TaskSubmitPage.tsx    # 任务提交页
│   │   ├── HistoryListPage.tsx   # 历史记录页
│   │   ├── EvaluationDetailPage.tsx # 评估详情页
│   │   └── ProjectListPage.tsx   # 项目管理页
│   ├── components/         # 通用组件
│   │   ├── TaskTable.tsx
│   │   ├── TaskFilters.tsx
│   │   ├── ScoreCard.tsx
│   │   ├── ImagePreview.tsx
│   │   ├── AnalysisPanel.tsx
│   │   └── ProjectForm.tsx
│   └── types/              # TypeScript类型
└── package.json
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 访问应用

http://localhost:5173

## 页面说明

### 提交任务

通过表单提交图片URL或上传本地图片，配合Prompt进行评估。

### 历史记录

查看所有历史评估任务，支持状态筛选、日期范围筛选和分页。

### 评估详情

查看单条评估任务的详细结果，包括CLIP评分、LLM分析和综合评分。

### 项目管理

创建和管理项目，用于分组管理评估任务。

## 开发

### 运行测试

```bash
npm test
```

### 代码格式

```bash
npm run lint
npm run format
```

### 构建生产版本

```bash
npm run build
```

## License

MIT
