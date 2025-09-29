# Chat Application - Full Stack AI Agent System

A sophisticated chat application featuring intelligent agent orchestration with a modern Next.js frontend and FastAPI backend powered by LangGraph and OpenAI.

## 🏗️ Architecture Overview

This application consists of two main components:

- **Frontend (chat-ui)**: Next.js 15 application with TypeScript and Tailwind CSS
- **Backend (chat-be)**: FastAPI application with intelligent agent orchestration using LangGraph

## 🎯 Frontend (chat-ui)

### User Flow

The frontend provides an intuitive chat interface with the following user journey:

#### 1. **Initial Access**

- Users land on a clean homepage with a chat icon
- Clicking the chat icon opens a resizable chat drawer
- The drawer can be resized by dragging the left edge

#### 2. **Thread Management**

- **Create New Thread**: Users can start new conversations with a single click
- **Thread List**: Sidebar displays all conversation threads with titles and timestamps
- **Thread Switching**: Seamless switching between different conversation threads
- **Thread Persistence**: All conversations are saved and can be resumed later

#### 3. **Message Interaction**

- **Text Messages**: Users can type and send text messages
- **File Uploads**: Drag-and-drop or click to upload documents (PDF, images, etc.)
- **Real-time Streaming**: Messages are streamed in real-time using Server-Sent Events (SSE)
- **Message History**: Complete conversation history is maintained and displayed

#### 4. **Response Modes**

- **Streaming Mode**: Real-time response streaming for immediate feedback
- **Async Mode**: For complex reports and analysis that require processing time
- **User Choice**: System intelligently detects when async processing is needed and offers user choice

#### 5. **Advanced Features**

- **Auto-scroll**: Automatic scrolling to latest messages
- **Manual Scroll**: Users can scroll up to view history while maintaining auto-scroll
- **Loading States**: Visual indicators for all operations
- **Error Handling**: Graceful error handling with retry options
- **Responsive Design**: Optimized for desktop and mobile devices

### Key Components

- **ChatDrawer**: Main chat interface component
- **ChatIcon**: Floating chat button
- **API Integration**: Comprehensive API service layer
- **File Upload**: Drag-and-drop file handling
- **Real-time Updates**: WebSocket and SSE integration

## 🤖 Backend (chat-be)

### Agent Architecture & Orchestration

The backend features a sophisticated multi-agent system built with LangGraph:

#### 1. **Supervisor Workflow** (Main Orchestrator)

The intelligent supervisor analyzes user messages and routes them to appropriate specialized agents:

**Key Features:**

- **Intent Analysis**: Analyzes user messages to determine the most appropriate workflow
- **Intelligent Routing**: Routes between simple chat and report researcher based on content analysis
- **Confidence Scoring**: Provides confidence scores for routing decisions
- **Context Preservation**: Maintains conversation history and context across interactions

**Routing Logic:**

- **Report Researcher**: Triggered by keywords like "report", "analysis", "research", "study", "SWOT", "market analysis"
- **Simple Chat**: Triggered by general conversation keywords like "hello", "calculate", "explain", "what time"
- **Default**: Falls back to simple chat for ambiguous cases

#### 2. **Simple Chat Agent**

Handles general conversation and simple tasks:

**Capabilities:**

- General Q&A and conversation
- Simple mathematical calculations
- Current time queries
- Context-aware responses

**Available Tools:**

- `get_current_time()`: Returns current date and time
- `calculate_simple_math(expression)`: Safely evaluates mathematical expressions

#### 3. **Report Researcher Agent**

Specialized workflow for research, analysis, and report writing:

**Multi-Phase Workflow:**

- **Analysis Phase**: Comprehensive topic analysis and report generation
- **Research Phase**: Data gathering and source recommendations
- **Writing Phase**: Professional report formatting and structure
- **Review Phase**: Quality assurance and improvement suggestions

**Analysis Types:**

- **General Analysis**: Standard research reports
- **Market Analysis**: Business and market research
- **Technical Analysis**: Technology and system analysis

**Available Tools:**

- `create_report_outline()`: Creates structured report outlines
- `suggest_research_sources()`: Recommends research sources and databases
- `analyze_data_patterns()`: Uses frameworks like SWOT, PEST, 5 Forces
- `format_report_section()`: Professional report section formatting

### API Endpoints

#### Thread Management

- `POST /api/threads` - Create new thread
- `GET /api/threads` - List all threads
- `GET /api/threads/{thread_id}` - Get thread details
- `GET /api/threads/{thread_id}/messages` - Get thread messages
- `DELETE /api/threads/{thread_id}` - Delete thread

#### Chat Messages

- `POST /api/chat` - Send chat message (sync)
- `POST /api/chat/stream` - Stream chat response (SSE)

#### Async Operations

- `POST /api/async/report` - Create async report task
- `POST /api/async/choice` - Handle response mode choice
- `GET /api/async/task/{task_id}` - Get task status
- `GET /api/async/thread/{thread_id}/tasks` - Get thread tasks
- `DELETE /api/async/task/{task_id}` - Cancel task

## 🚀 Local Development

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.8+ (for backend)
- **PostgreSQL** (for database)
- **OpenAI API Key** (for AI functionality)

### Frontend Setup (chat-ui)

1. **Navigate to frontend directory:**

   ```bash
   cd chat-ui
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Set up environment variables:**
   Create `.env.local` file:

   ```bash
   NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000
   ```

4. **Start development server:**

   ```bash
   npm run dev
   ```

5. **Access the application:**
   Open [http://localhost:3000](http://localhost:3000) in your browser

### Backend Setup (chat-be)

1. **Navigate to backend directory:**

   ```bash
   cd chat-be
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create `.env` file:

   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/threads_db
   ```

5. **Start PostgreSQL database:**
   Make sure PostgreSQL is running and create the database:

   ```sql
   CREATE DATABASE threads_db;
   ```

6. **Start the development server:**

   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access API documentation:**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Docker Setup (Alternative)

1. **Using Docker Compose:**

   ```bash
   # From project root
   docker-compose up
   ```

2. **Individual Docker builds:**

   ```bash
   # Backend
   cd chat-be
   docker build -t chat-be .
   docker run -p 8000:8000 chat-be

   # Frontend
   cd chat-ui
   docker build -t chat-ui .
   docker run -p 3000:3000 chat-ui
   ```

## 🔧 Configuration

### Environment Variables

#### Frontend (.env.local)

```bash
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000
```

#### Backend (.env)

```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/threads_db
```

### Database Setup

The application uses PostgreSQL with automatic:

- Database creation (`threads_db`)
- Table creation on startup
- Connection pooling for performance

## 🧪 Testing

### Frontend Testing

```bash
cd chat-ui
npm run test
```

### Backend Testing

```bash
cd chat-be
python -m pytest
```

### API Testing

Use the provided test utilities in `chat-ui/src/app/utils/testApi.ts`:

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

## 📁 Project Structure

```
full-agent/
├── chat-ui/                 # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/     # React components
│   │   │   ├── services/        # API services
│   │   │   ├── utils/          # Utility functions
│   │   │   └── hooks/          # Custom React hooks
│   │   └── ...
│   ├── package.json
│   └── README.md
├── chat-be/                 # FastAPI Backend
│   ├── workflows/            # LangGraph workflows
│   │   ├── supervisor_workflow.py
│   │   ├── simple_chat_subgraph.py
│   │   └── report_researcher_subgraph.py
│   ├── routes/               # API routes
│   ├── models/               # Database models
│   ├── app.py               # FastAPI application
│   └── requirements.txt
├── docker-compose.yaml      # Docker orchestration
└── README.md               # This file
```

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Set production environment variables
2. **Database**: Use production PostgreSQL instance
3. **API Keys**: Secure OpenAI API key management
4. **CORS**: Configure CORS for production domains
5. **SSL**: Enable HTTPS for secure communication

### Scaling

- **Horizontal Scaling**: Multiple backend instances with load balancing
- **Database**: PostgreSQL connection pooling
- **Caching**: Redis for session and conversation caching
- **CDN**: Static asset delivery optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the API documentation at `/docs`
2. Review the testing guides
3. Check the Docker setup documentation
4. Open an issue on the repository

---

**Built with ❤️ using Next.js, FastAPI, LangGraph, and OpenAI**
