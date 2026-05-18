/**
 * WebSocket client for real-time task updates
 */

import type { WSMessage, WSMessageType, TaskStatus, ProgressInfo, WSResultData, WSErrorData } from '../types';

type MessageHandler = (message: WSMessage) => void;

const WS_BASE_URL = import.meta.env.VITE_WS_URL || '';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private taskId: string | null = null;
  private handlers: Map<WSMessageType, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  /**
   * Connect to WebSocket for a specific task
   */
  connect(taskId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.taskId === taskId) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Already connecting'));
        return;
      }

      this.isConnecting = true;
      this.taskId = taskId;

      const wsUrl = `${WS_BASE_URL}/ws/${taskId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          this.notifyHandlers(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        reject(error);
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.handleClose();
      };
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.taskId = null;
      this.reconnectAttempts = 0;
    }
  }

  /**
   * Subscribe to a specific message type
   */
  on(type: WSMessageType, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  /**
   * Subscribe to status updates
   */
  onStatus(handler: (status: TaskStatus, progress?: ProgressInfo) => void): () => void {
    return this.on('status', (message) => {
      const data = message.data as { status: TaskStatus; progress?: ProgressInfo };
      handler(data.status, data.progress);
    });
  }

  /**
   * Subscribe to result updates
   */
  onResult(handler: (result: WSResultData) => void): () => void {
    return this.on('result', (message) => {
      handler(message.data as WSResultData);
    });
  }

  /**
   * Subscribe to error updates
   */
  onError(handler: (error: WSErrorData) => void): () => void {
    return this.on('error', (message) => {
      handler(message.data as WSErrorData);
    });
  }

  private notifyHandlers(message: WSMessage): void {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }
  }

  private handleClose(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.taskId) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      setTimeout(() => {
        if (this.taskId) {
          this.connect(this.taskId).catch(console.error);
        }
      }, delay);
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
export default wsClient;
