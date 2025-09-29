# Chat UI API Integration

This document describes how the chat-ui frontend integrates with the chat-be backend API.

## Features Implemented

### 1. Thread Management

- ✅ Create new conversation threads
- ✅ List all threads with summaries
- ✅ Load thread messages
- ✅ Switch between threads
- ✅ Real-time thread updates

### 2. Chat Messaging

- ✅ Send text messages
- ✅ Upload and send documents
- ✅ Real-time message display
- ✅ Message history persistence

### 3. Streaming Chat

- ✅ Server-Sent Events (SSE) streaming
- ✅ Real-time response updates
- ✅ Streaming indicators in UI
- ✅ Error handling for stream failures

### 4. Async Chat

- ✅ Async report generation
- ✅ User choice for response mode (stream vs async)
- ✅ Task status polling
- ✅ Progress indicators
- ✅ Result display when completed

### 5. Error Handling & Loading States

- ✅ Loading spinners for all operations
- ✅ Error messages with retry options
- ✅ Network error handling
- ✅ Graceful fallbacks

## API Endpoints Used

### Thread Management

- `POST /api/threads` - Create new thread
- `GET /api/threads` - List all threads
- `GET /api/threads/{thread_id}` - Get thread details
- `GET /api/threads/{thread_id}/messages` - Get thread messages
- `DELETE /api/threads/{thread_id}` - Delete thread

### Chat Messages

- `POST /api/chat` - Send chat message (sync)
- `POST /api/chat/stream` - Stream chat response (SSE)

### Async Operations

- `POST /api/async/report` - Create async report task
- `POST /api/async/choice` - Handle response mode choice
- `GET /api/async/task/{task_id}` - Get task status
- `GET /api/async/thread/{thread_id}/tasks` - Get thread tasks
- `DELETE /api/async/task/{task_id}` - Cancel task

## Configuration

### Environment Variables

Set the following environment variable to configure the API URL:

```bash
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000
```

### Default Configuration

If no environment variable is set, the app defaults to `http://localhost:8000`.

## Usage Examples

### Basic Chat Flow

1. User opens chat drawer
2. System loads existing threads
3. User can create new thread or select existing
4. User types message and sends
5. System streams response in real-time

### Async Report Flow

1. User sends message containing "report", "analysis", or "research"
2. System detects async intent and creates interruption
3. User chooses between "streaming" or "async" response mode
4. System processes request based on choice
5. For async: polls task status until completion
6. For streaming: shows real-time progress

### Error Handling

- Network errors show retry buttons
- Loading states prevent multiple submissions
- Graceful degradation for API failures

## Testing

Use the test utilities in `src/app/utils/testApi.ts`:

```typescript
import {
  testApiConnection,
  testStreamingChat,
  testAsyncReport,
} from "../utils/testApi";

// Test basic API connection
const result = await testApiConnection();

// Test streaming chat
const streamResult = await testStreamingChat(threadId);

// Test async report
const asyncResult = await testAsyncReport(threadId);
```

## File Structure

```
src/app/
├── components/
│   └── ChatDrawer.tsx          # Main chat interface
├── services/
│   └── chatApi.ts              # API service layer
├── config/
│   └── api.ts                  # API configuration
├── utils/
│   └── testApi.ts              # Test utilities
└── hooks/
    └── useFileUpload.ts        # File upload handling
```

## Key Components

### ChatApiService

Centralized service for all API communications with:

- Type-safe interfaces
- Error handling
- Request/response transformation
- Streaming support

### ChatDrawer

Main chat interface with:

- Thread management
- Message display
- Streaming indicators
- Async task handling
- Error states

### State Management

React state for:

- Threads and messages
- Loading and error states
- Streaming status
- Async task progress

## Development Notes

1. **CORS**: Ensure chat-be allows requests from chat-ui origin
2. **Environment**: Set `NEXT_PUBLIC_CHAT_API_URL` for production
3. **Testing**: Use test utilities to verify API integration
4. **Error Handling**: All API calls include proper error handling
5. **Loading States**: UI shows appropriate loading indicators

## Next Steps

- [ ] Add authentication integration
- [ ] Implement real-time notifications
- [ ] Add message search functionality
- [ ] Implement message reactions
- [ ] Add file preview capabilities
