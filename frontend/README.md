# Agent图像评估系统 - 前端

## 技术栈

- React 18
- Ant Design 6
- TypeScript
- Vite
- React Router 6

## 项目结构

```
frontend/
├── src/
│   ├── main.tsx           # 入口文件
│   ├── App.tsx            # 根组件
│   ├── api/               # API调用
│   │   ├── client.ts      # HTTP客户端
│   │   └── websocket.ts   # WebSocket客户端
│   ├── pages/             # 页面组件
│   ├── components/        # 通用组件
│   ├── types/             # TypeScript类型定义
│   └── __tests__/         # 组件测试
├── public/
├── cypress/               # E2E测试
├── package.json
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

### 3. 构建生产版本

```bash
npm run build
```

## 环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

## 测试

```bash
# 运行组件测试
npm test

# 运行E2E测试
npm run cypress:run

# 打开E2E测试界面
npm run cypress:open
```

## 页面说明

- `/` - 任务提交页面
- `/history` - 历史记录列表
- `/detail/:taskId` - 评估详情页面
- `/projects` - 项目管理页面
