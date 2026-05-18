/**
 * REST API client for backend communication
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  TaskCreateRequest,
  TaskCreateResponse,
  TaskStatusResponse,
  TaskListResponse,
  TaskListItem,
  EvaluationResultResponse,
  ProjectCreateRequest,
  ProjectWithStats,
  ProjectListResponse,
  TaskFilterParams,
  ErrorResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response?.data?.error) {
          const { code, message } = error.response.data.error;
          return Promise.reject(new Error(`${code}: ${message}`));
        }
        return Promise.reject(error);
      }
    );
  }

  // --- Task APIs ---

  /**
   * Create a new evaluation task
   */
  async createTask(data: TaskCreateRequest): Promise<TaskCreateResponse> {
    const response = await this.client.post<TaskCreateResponse>('/tasks', data);
    return response.data;
  }

  /**
   * Get task status by ID
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await this.client.get<TaskStatusResponse>(`/tasks/${taskId}`);
    return response.data;
  }

  /**
   * Get evaluation result by task ID
   */
  async getTaskResult(taskId: string): Promise<EvaluationResultResponse> {
    const response = await this.client.get<EvaluationResultResponse>(
      `/tasks/${taskId}/result`
    );
    return response.data;
  }

  /**
   * List tasks with pagination and filtering
   */
  async listTasks(params: TaskFilterParams = {}): Promise<TaskListResponse> {
    const response = await this.client.get<TaskListResponse>('/tasks', { params });
    return response.data;
  }

  // --- Project APIs ---

  /**
   * Create a new project
   */
  async createProject(data: ProjectCreateRequest): Promise<ProjectWithStats> {
    const response = await this.client.post<ProjectWithStats>('/projects', data);
    return response.data;
  }

  /**
   * Get project by ID
   */
  async getProject(projectId: string): Promise<ProjectWithStats> {
    const response = await this.client.get<ProjectWithStats>(`/projects/${projectId}`);
    return response.data;
  }

  /**
   * List projects with pagination
   */
  async listProjects(limit = 20, offset = 0): Promise<ProjectListResponse> {
    const response = await this.client.get<ProjectListResponse>('/projects', {
      params: { limit, offset },
    });
    return response.data;
  }

  // --- Health API ---

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
