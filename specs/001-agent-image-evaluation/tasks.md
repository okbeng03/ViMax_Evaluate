# Tasks: Agent图像评估系统

**Input**: Design documents from `/specs/001-agent-image-evaluation/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend project structure in `backend/` per implementation plan
- [x] T002 Create frontend project structure in `frontend/` using Vite + React 18 + Ant Design 6
- [x] T003 [P] Initialize Python 3.13 project with FastAPI dependencies in `backend/requirements.txt`
- [x] T004 [P] Initialize Node.js project with React 18 + Ant Design 6 in `frontend/package.json`
- [x] T005 Create data directory `data/` for SQLite database

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [x] T006 Setup SQLite database with SQLAlchemy in `backend/src/db/database.py`
- [x] T007 [P] Create SQLAlchemy models for Project, EvaluationTask, EvaluationResult in `backend/src/db/models.py`
- [x] T008 [P] Create Pydantic models for API requests/responses in `backend/src/models/schemas.py`
- [x] T009 [P] Create configuration management with pydantic-settings in `backend/src/config.py`
- [x] T010 [P] Setup logging infrastructure with structured logging in `backend/src/utils/logger.py`
- [x] T011 Create FastAPI application entry point in `backend/src/main.py`
- [x] T012 [P] Setup WebSocket manager for real-time communication in `backend/src/services/websocket_manager.py`
- [x] T013 Create error handling and exception classes in `backend/src/utils/exceptions.py`
- [x] T014 [P] Add API contract tests for endpoints in `backend/tests/contract/` (see api-contracts.md)

### Frontend Foundation

- [x] T015 [P] Setup React Router and page structure in `frontend/src/App.tsx`
- [x] T016 [P] Create TypeScript type definitions in `frontend/src/types/index.ts`
- [x] T017 [P] Create API client for REST endpoints in `frontend/src/api/client.ts`
- [x] T018 Create WebSocket client for real-time updates in `frontend/src/api/websocket.ts`
- [x] T019 Setup Ant Design 6 theme provider in `frontend/src/main.tsx`
- [x] T020 [P] Add frontend component tests with React Testing Library in `frontend/src/__tests__/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 提交图像评估任务 (Priority: P1) 🎯 MVP

**Goal**: 用户通过API提交图片和prompt，系统返回唯一任务ID供后续追踪

**Independent Test**: 可通过API直接提交任务并验证返回的任务ID

### Implementation for User Story 1

- [x] T021 [P] [US1] Create task creation endpoint POST /api/v1/tasks in `backend/src/routers/tasks.py`
- [x] T022 [P] [US1] Implement Project model and CRUD operations in `backend/src/services/project_service.py`
- [x] T023 [P] [US1] Implement task repository for database operations in `backend/src/services/task_repository.py`
- [x] T024 [US1] Create async task queue with asyncio.Queue in `backend/src/services/task_queue.py`
- [x] T025 [US1] Implement task manager for task lifecycle in `backend/src/services/task_manager.py`
- [x] T026 [US1] Add task creation validation (image or base64 required, prompt required)
- [x] T027 [US1] Integrate WebSocket manager for task status updates

### Testing for User Story 1

- [x] T028 [US1] Add unit tests for task creation in `backend/tests/unit/test_tasks.py`
- [x] T029 [US1] Verify API returns task_id within 5 seconds (SC-001)

**Checkpoint**: User Story 1 should be fully functional - tasks can be submitted and tracked

---

## Phase 4: User Story 2 - 实时追踪评估进度 (Priority: P1)

**Goal**: 用户通过WebSocket实时接收评估任务的状态更新和最终结果

**Independent Test**: 可通过WebSocket连接验证任务状态推送功能

### Implementation for User Story 2

- [x] T030 [P] [US2] Implement CLIP evaluator with open_clip_torch in `backend/src/services/clip_evaluator.py`
- [x] T031 [P] [US2] Implement ComfyUI client for Qwen VL workflow in `backend/src/services/comfyui_client.py`
- [x] T032 [P] [US2] Implement LLM evaluator with LangChain in `backend/src/services/llm_evaluator.py`
- [x] T033 [US2] Create evaluation pipeline orchestrator in `backend/src/services/evaluation_pipeline.py`
- [x] T034 [US2] Implement WebSocket endpoint /ws/{task_id} in `backend/src/routers/websocket.py`
- [x] T035 [US2] Add progress tracking with phases (clip_evaluation, llm_evaluation)
- [x] T036 [US2] Add result and error message broadcasting

### Testing for User Story 2

- [x] T037 [US2] Add WebSocket integration tests in `backend/tests/integration/test_websocket.py`
- [x] T038 [US2] Verify WebSocket push latency < 1 second (SC-005)
- [x] T039 [US2] Add evaluator unit tests in `backend/tests/unit/test_evaluators.py`

**Checkpoint**: User Story 2 should be fully functional - real-time progress tracking works

---

## Phase 5: User Story 3 - 查看历史评估记录 (Priority: P2)

**Goal**: 用户通过前端页面查看所有历史评估任务及其结果

**Independent Test**: 可通过前端页面查看任务列表，支持分页和筛选

### Backend for User Story 3

- [x] T040 [P] [US3] Implement GET /api/v1/tasks endpoint with pagination and filtering in `backend/src/routers/tasks.py`
- [x] T041 [P] [US3] Implement GET /api/v1/projects endpoint with pagination in `backend/src/routers/projects.py`
- [x] T042 [US3] Add date range and score filtering to task query

### Frontend for User Story 3

- [x] T043 [P] [US3] Create ProjectListPage component in `frontend/src/pages/ProjectListPage.tsx`
- [x] T044 [P] [US3] Create HistoryListPage component with pagination in `frontend/src/pages/HistoryListPage.tsx`
- [x] T045 [P] [US3] Create TaskTable component with status badges in `frontend/src/components/TaskTable.tsx`
- [x] T046 [US3] Add filtering controls (date range, status, project) in `frontend/src/components/TaskFilters.tsx`

### Testing for User Story 3

- [ ] T047 [US3] Add E2E tests for history list in `frontend/cypress/e2e/history.cy.ts`
- [x] T048 [US3] Verify pagination load latency < 2 seconds (SC-004)

**Checkpoint**: User Story 3 should be fully functional - history list with filtering works

---

## Phase 6: User Story 4 - 查看评估详情 (Priority: P2)

**Goal**: 用户点击某条历史记录查看完整的评估报告

**Independent Test**: 可通过点击列表项查看详情页面，展示完整评估数据

### Backend for User Story 4

- [x] T049 [P] [US4] Implement GET /api/v1/tasks/{task_id} endpoint in `backend/src/routers/tasks.py`
- [x] T050 [P] [US4] Implement GET /api/v1/tasks/{task_id}/result endpoint in `backend/src/routers/tasks.py`
- [x] T051 [P] [US4] Implement GET /api/v1/projects/{project_id} endpoint in `backend/src/routers/projects.py`

### Frontend for User Story 4

- [x] T052 [P] [US4] Create EvaluationDetailPage component in `frontend/src/pages/EvaluationDetailPage.tsx`
- [x] T053 [P] [US4] Create ScoreCard component for displaying scores in `frontend/src/components/ScoreCard.tsx`
- [x] T054 [P] [US4] Create ImagePreview component for displaying generated image in `frontend/src/components/ImagePreview.tsx`
- [x] T055 [P] [US4] Create AnalysisPanel component for LLM analysis in `frontend/src/components/AnalysisPanel.tsx`
- [x] T056 [US4] Add navigation from HistoryListPage to EvaluationDetailPage
- [x] T057 [US4] Add real-time WebSocket updates on detail page

### Testing for User Story 4

- [ ] T058 [US4] Add E2E tests for detail page in `frontend/cypress/e2e/detail.cy.ts`

**Checkpoint**: User Story 4 should be fully functional - detailed evaluation view works

---

## Phase 7: Project Management (Supporting Feature)

**Goal**: 支持创建和管理项目/批次来分组评估任务

- [x] T059 [P] Implement POST /api/v1/projects endpoint in `backend/src/routers/projects.py`
- [x] T060 [P] Add task count and average score aggregation to project queries
- [x] T061 [P] Create ProjectForm component in `frontend/src/components/ProjectForm.tsx`
- [x] T062 [US3] Integrate project selection in task submission form
- [x] T063 [US3] Add project filter in history list

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation

- [x] T064 [P] Update README.md files in `backend/` and `frontend/`
- [ ] T065 [P] Add API documentation with examples in `backend/src/routers/`

### Quality

- [ ] T066 Add input validation for image URLs and base64 data
- [ ] T067 Add rate limiting for task submission
- [ ] T068 Add request timeout handling for ComfyUI and LLM calls
- [ ] T069 Add retry logic for transient failures

### Performance

- [ ] T070 [P] Add database indexes for common query patterns
- [ ] T071 [P] Implement response caching for project statistics
- [ ] T072 Optimize image loading in frontend with lazy loading

### Testing (Supplementary)

- [ ] T073 [P] Add backend integration tests in `backend/tests/integration/`
- [ ] T074 [P] Add end-to-end tests with Playwright/Cypress in `frontend/e2e/`
- [ ] T075 Run quickstart.md validation

### Operations

- [x] T076 Add health check endpoint in `backend/src/routers/health.py`
- [ ] T077 Add metrics collection for monitoring
- [ ] T078 Setup Docker configuration for deployment (optional, see Assumptions)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories (MVP)
- **User Story 2 (P1)**: Can start after Foundational - Evaluators can be developed independently
- **User Story 3 (P2)**: Can start after Foundational - Can work in parallel with US4
- **User Story 4 (P2)**: Can start after Foundational - Can work in parallel with US3

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- US1 and US2 can proceed in parallel after Foundational
- US3 and US4 can proceed in parallel after Foundational
- All evaluators (clip, comfyui, llm) can be implemented in parallel

### Constitution Alignment

Per the project constitution (章程序程), testing tasks have been integrated into each user story phase:
- **Phase 2**: Contract tests (T014) and component tests (T020) as prerequisites
- **US1**: Unit tests (T028) + Performance verification (T029, SC-001)
- **US2**: WebSocket integration tests (T037) + Latency verification (T038, SC-005) + Evaluator unit tests (T039)
- **US3**: E2E tests (T047) + Pagination latency verification (T048, SC-004)
- **US4**: E2E tests (T058)
- **Phase 8**: Supplementary integration and E2E tests (T069-T071)

---

## Parallel Example: User Story 1 + 2

```bash
# Launch in parallel:
Task T021: Create task creation endpoint POST /api/v1/tasks
Task T030: Implement CLIP evaluator with open_clip_torch
Task T031: Implement ComfyUI client for Qwen VL workflow
Task T032: Implement LLM evaluator with LangChain
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (task submission)
4. Complete Phase 4: User Story 2 (evaluation + WebSocket)
5. **STOP and VALIDATE**: Full evaluation pipeline works end-to-end
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Tasks can be submitted → Deploy/Demo
3. Add User Story 2 → Full evaluation works → Deploy/Demo (MVP!)
4. Add User Story 3 → History list in frontend → Deploy/Demo
5. Add User Story 4 → Detailed view in frontend → Deploy/Demo

### Suggested MVP Scope

**Core MVP (US1 + US2)**: 提交评估任务 + 实时追踪进度 + CLIP/LLM评估

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
