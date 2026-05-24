/**
 * TypeScript type definitions for Agent图像评估系统
 */

/** Task status enumeration */
export type TaskStatus = 'pending' | 'queued' | 'processing' | 'completed' | 'failed';

/** CLIP interpretation values */
export type ClipInterpretation = 'consistent' | 'inconsistent' | 'ambiguous';

/** LLM consistency values */
export type LLMConsistency = 'consistent' | 'partially_consistent' | 'inconsistent';

/** Project entity */
export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

/** Project with statistics */
export interface ProjectWithStats extends Project {
  task_count: number;
  avg_score?: number;
}

/** Create task request */
export interface TaskCreateRequest {
  project_id?: string;
  image_url?: string;
  image_base64?: string;
  hash_id?: string;
  prompt: string;
}

/** Create task response */
export interface TaskCreateResponse {
  task_id: string;
  status: TaskStatus;
  created_at: string;
}

/** Progress information */
export interface ProgressInfo {
  current_phase: string;
  phases_completed: string[];
  phases_total: number;
  progress_percent: number;
}

/** Task status response */
export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  image_url?: string;
  image_base64?: string;
  hash_id?: string;
  prompt?: string;
  project_id?: string;
  overall_score?: number;
  progress?: ProgressInfo;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

/** Task list item */
export interface TaskListItem {
  task_id: string;
  status: TaskStatus;
  project_id?: string;
  prompt_summary: string;
  overall_score?: number;
  clip_score?: number;
  llm_score?: number;
  created_at: string;
}

/** Paginated task list response */
export interface TaskListResponse {
  tasks: TaskListItem[];
  total: number;
  limit: number;
  offset: number;
}

/** LLM 维度评分 */
export interface DimensionScore {
  subject_consistency: number;
  action_consistency: number;
  attribute_consistency: number;
  spatial_consistency: number;
  composition_consistency: number;
  lighting_consistency: number;
  style_consistency: number;
  anatomy_quality: number;
  artifact_quality: number;
}

/** LLM 需求匹配项 */
export interface RequirementMatch {
  item: string;
  status: 'matched' | 'missing' | 'incorrect';
  confidence?: number;
  evidence?: string;
}

/** Evaluation result response */
export interface EvaluationResultResponse {
  task_id: string;
  prompt?: string;
  project_id?: string;
  clip_score: number;
  clip_interpretation: string;
  structured_description: string;
  llm_analysis: string;
  llm_consistency: string;
  overall_score: number;
  processing_time_ms: number;
  created_at: string;
  // LLM 扩展字段
  llm_overall_score?: number;
  llm_dimension_scores?: DimensionScore;
  llm_matched_requirements?: RequirementMatch[];
  llm_missing_requirements?: RequirementMatch[];
  llm_incorrect_requirements?: RequirementMatch[];
  llm_extra_elements?: string[];
  llm_critical_failures?: string[];
}

/** WebSocket message types */
export type WSMessageType = 'status' | 'progress' | 'result' | 'error';

/** WebSocket message */
export interface WSMessage {
  type: WSMessageType;
  task_id: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/** WebSocket status data */
export interface WSStatusData {
  status: TaskStatus;
  progress?: ProgressInfo;
}

/** WebSocket result data */
export interface WSResultData {
  clip_score: number;
  clip_interpretation: string;
  overall_score: number;
  llm_score: number;
  llm_description: string;
}

/** WebSocket error data */
export interface WSErrorData {
  error_type: string;
  message: string;
}

/** Error detail */
export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/** Error response */
export interface ErrorResponse {
  error: ErrorDetail;
}

/** Create project request */
export interface ProjectCreateRequest {
  name: string;
  description?: string;
}

/** Project list response */
export interface ProjectListResponse {
  projects: ProjectWithStats[];
  total: number;
}

/** Task filter parameters */
export interface TaskFilterParams {
  project_id?: string;
  status?: TaskStatus;
  limit?: number;
  offset?: number;
  start_date?: string;
  end_date?: string;
}
