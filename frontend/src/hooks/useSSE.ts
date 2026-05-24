/**
 * Global singleton SSE (Server-Sent Events) client.
 *
 * Only one HTTP connection is opened to the backend /events endpoint.
 * Components subscribe/unsubscribe via the useSSE hook — no duplicate connections.
 */

import { useEffect, useRef } from 'react';

/** SSE event data structure from backend */
export interface SSEEvent {
  type: string;
  data: {
    task_id: string;
    overall_score?: number;
    status?: string;
  };
  timestamp: string;
}

type EventHandler = (event: SSEEvent) => void;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const SSE_URL = `${API_BASE_URL}/events`;
const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;

/* ------- Global singleton SSE client ------- */
type ListenerEntry = { eventType: string; handler: EventHandler };

class SSEClient {
  private listeners: ListenerEntry[] = [];
  private controller: AbortController | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private disconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private started = false;
  private reconnectAttempts = 0;

  subscribe(eventType: string, handler: EventHandler): () => void {
    this.listeners.push({ eventType, handler });
    // Cancel any pending disconnect (e.g. during page navigation)
    if (this.disconnectTimer) {
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }
    if (!this.started) this.connect();
    return () => this.unsubscribe(eventType, handler);
  }

  private unsubscribe(eventType: string, handler: EventHandler) {
    this.listeners = this.listeners.filter(
      (e) => !(e.eventType === eventType && e.handler === handler),
    );
    // Delay disconnect — a new subscriber may arrive soon
    // (page navigation, React Strict Mode double-fire, etc.)
    if (this.listeners.length === 0) {
      this.disconnectTimer = setTimeout(() => this.disconnect(), 300);
    }
  }

  private connect() {
    this.started = true;
    this.reconnectAttempts = 0;
    this.controller?.abort();
    this.controller = new AbortController();

    const run = () => {
      fetch(SSE_URL, {
        signal: this.controller!.signal,
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            throw new Error(`SSE connection failed: ${response.status}`);
          }
          // Connection established — reset backoff
          this.reconnectAttempts = 0;

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop() || '';

            for (const part of parts) {
              if (part.startsWith(': ')) continue; // heartbeat
              const dataMatch = part.match(/^data: (.+)$/m);
              if (!dataMatch) continue;

              try {
                const event = JSON.parse(dataMatch[1]) as SSEEvent;
                this.dispatch(event);
              } catch {
                // skip malformed
              }
            }
          }
        })
        .catch((error) => {
          if (error.name === 'AbortError') return;
          console.warn('SSE connection error, reconnecting...', error);
        })
        .finally(() => {
          // Reconnect with exponential backoff if still has listeners
          if (this.listeners.length > 0) {
            this.reconnectAttempts++;
            const delay = Math.min(
              INITIAL_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts - 1),
              MAX_RECONNECT_DELAY,
            );
            this.reconnectTimer = setTimeout(run, delay);
          } else {
            this.started = false;
          }
        });
    };

    run();
  }

  private dispatch(event: SSEEvent) {
    // Copy list in case handlers modify subscriptions
    for (const entry of [...this.listeners]) {
      if (entry.eventType === event.type) {
        entry.handler(event);
      }
    }
  }

  private disconnect() {
    this.started = false;
    this.reconnectAttempts = 0;
    this.controller?.abort();
    this.controller = null;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.disconnectTimer) {
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }
  }
}

const globalSSEClient = new SSEClient();

/* ------- React hook ------- */

/**
 * React hook for listening to SSE events via the global singleton connection.
 *
 * @param eventType - Event type to filter (e.g. 'task_completed', 'task_updated')
 * @param handler  - Callback invoked when a matching event arrives
 * @param enabled  - Whether to subscribe (default: true)
 */
export function useSSE(
  eventType: string,
  handler: EventHandler,
  enabled: boolean = true,
) {
  // Use refs so we can update handler and enabled without re-subscribing
  const handlerRef = useRef(handler);
  handlerRef.current = handler;
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;

  useEffect(() => {
    const wrappedHandler: EventHandler = (event) => {
      if (enabledRef.current) {
        handlerRef.current(event);
      }
    };

    const unsubscribe = globalSSEClient.subscribe(eventType, wrappedHandler);
    return unsubscribe;
  }, [eventType]);
}
