/**
 * Chat API service for communicating with chat-be backend
 */

import API_CONFIG from "../config/api";

export interface CreateThreadRequest {
  title?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateThreadResponse {
  thread_id: string;
  title: string;
  created_at: string;
  last_message_at: string;
}

export interface ThreadSummary {
  thread_id: string;
  title: string;
  created_at: string;
  last_message_at: string;
  message_count: number;
  last_message_preview?: string;
}

export interface MessageResponse {
  message_id: string;
  content: string;
  is_user: boolean;
  message_type: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface ThreadDetails {
  thread_id: string;
  title: string;
  created_at: string;
  last_message_at: string;
  messages: MessageResponse[];
}

export interface ChatMessageRequest {
  thread_id: string;
  content: string;
  message_type?: string;
  document_urls?: string[];
  metadata?: Record<string, unknown>;
  context?: Record<string, unknown>;
  response_mode?: "sync" | "stream" | "async";
}

export interface ChatMessageResponse {
  message_id: string;
  thread_id: string;
  content: string;
  is_user: boolean;
  message_type: string;
  created_at: string;
  ai_response?: string;
  metadata?: Record<string, unknown>;
}

export interface AsyncReportRequest {
  thread_id: string;
  content: string;
  message_type?: string;
  document_urls?: string[];
  metadata?: Record<string, unknown>;
  context?: Record<string, unknown>;
  priority?: "low" | "normal" | "high";
}

export interface AsyncReportResponse {
  task_id: string;
  thread_id: string;
  status: string;
  message: string;
  estimated_completion_time?: string;
  created_at: string;
}

export interface AsyncTaskStatus {
  task_id: string;
  thread_id: string;
  status: string;
  progress?: number;
  message: string;
  result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface ResponseModeChoice {
  task_id: string;
  response_mode: "stream" | "async";
  user_id?: string;
}

export interface InterruptionResponse {
  task_id: string;
  thread_id: string;
  status: string;
  message: string;
  choices: string[];
  created_at: string;
}

// Streaming response types
export interface StreamChunk {
  type: "metadata" | "content" | "error" | "end";
  data: {
    content?: string;
    is_partial?: boolean;
    error_message?: string;
    status?: string;
    [key: string]: unknown;
  };
  timestamp: string;
}

class ChatApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  // Thread Management
  async createThread(
    request: CreateThreadRequest
  ): Promise<CreateThreadResponse> {
    const response = await fetch(`${this.baseUrl}/api/threads`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create thread: ${response.statusText}`);
    }

    return response.json();
  }

  async listThreads(): Promise<ThreadSummary[]> {
    const response = await fetch(`${this.baseUrl}/api/threads`);

    if (!response.ok) {
      throw new Error(`Failed to list threads: ${response.statusText}`);
    }

    return response.json();
  }

  async getThread(threadId: string): Promise<ThreadDetails> {
    const response = await fetch(`${this.baseUrl}/api/threads/${threadId}`);

    if (!response.ok) {
      throw new Error(`Failed to get thread: ${response.statusText}`);
    }

    return response.json();
  }

  async getThreadMessages(threadId: string): Promise<MessageResponse[]> {
    const response = await fetch(
      `${this.baseUrl}/api/threads/${threadId}/messages`
    );

    if (!response.ok) {
      throw new Error(`Failed to get thread messages: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteThread(
    threadId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/threads/${threadId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Failed to delete thread: ${response.statusText}`);
    }

    return response.json();
  }

  // Chat Messages
  async sendChatMessage(
    request: ChatMessageRequest
  ): Promise<ChatMessageResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to send chat message: ${response.statusText}`);
    }

    return response.json();
  }

  // Streaming Chat
  async streamChatMessage(
    request: ChatMessageRequest,
    onChunk: (chunk: StreamChunk) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to start streaming: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader available");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = line.slice(6); // Remove 'data: ' prefix
              if (data.trim()) {
                const chunk: StreamChunk = JSON.parse(data);
                onChunk(chunk);
              }
            } catch (error) {
              console.error("Error parsing stream chunk:", error);
              onError?.(new Error("Failed to parse stream data"));
            }
          }
        }
      }
    } catch (error) {
      onError?.(error as Error);
    }
  }

  // Async Chat
  async createAsyncReport(
    request: AsyncReportRequest
  ): Promise<InterruptionResponse> {
    const response = await fetch(`${this.baseUrl}/api/async/report`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create async report: ${response.statusText}`);
    }

    return response.json();
  }

  async handleResponseModeChoice(
    choice: ResponseModeChoice
  ): Promise<AsyncReportResponse> {
    const response = await fetch(`${this.baseUrl}/api/async/choice`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(choice),
    });

    if (!response.ok) {
      throw new Error(
        `Failed to handle response mode choice: ${response.statusText}`
      );
    }

    return response.json();
  }

  async getTaskStatus(taskId: string): Promise<AsyncTaskStatus> {
    const response = await fetch(`${this.baseUrl}/api/async/task/${taskId}`);

    if (!response.ok) {
      throw new Error(`Failed to get task status: ${response.statusText}`);
    }

    return response.json();
  }

  async getThreadTasks(threadId: string): Promise<AsyncTaskStatus[]> {
    const response = await fetch(
      `${this.baseUrl}/api/async/thread/${threadId}/tasks`
    );

    if (!response.ok) {
      throw new Error(`Failed to get thread tasks: ${response.statusText}`);
    }

    return response.json();
  }

  async cancelTask(
    taskId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/async/task/${taskId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Failed to cancel task: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const chatApi = new ChatApiService();
export default chatApi;
