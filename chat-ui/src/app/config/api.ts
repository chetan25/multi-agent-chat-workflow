/**
 * API Configuration for chat-be backend
 */

export const API_CONFIG = {
  // Default to localhost for development
  BASE_URL: process.env.NEXT_PUBLIC_CHAT_API_URL || "http://localhost:8000",

  // API endpoints
  ENDPOINTS: {
    THREADS: "/api/threads",
    CHAT: "/api/chat",
    CHAT_STREAM: "/api/chat/stream",
    ASYNC_REPORT: "/api/async/report",
    ASYNC_CHOICE: "/api/async/choice",
    ASYNC_TASK: "/api/async/task",
    ASYNC_THREAD_TASKS: "/api/async/thread",
  },

  // Request timeouts
  TIMEOUTS: {
    DEFAULT: 30000, // 30 seconds
    STREAM: 60000, // 60 seconds for streaming
    POLL: 2000, // 2 seconds for polling
  },
} as const;

export default API_CONFIG;
