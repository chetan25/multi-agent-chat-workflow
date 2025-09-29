# Chat-BE Supervisor Workflow System

This directory contains a sophisticated chat workflow system built with LangGraph, LangChain, and OpenAI. The system features an intelligent supervisor that automatically routes user messages between simple chat and report researcher workflows based on message analysis.

## Architecture Overview

The chat workflow system is designed with intelligent routing and modularity in mind:

- **Supervisor Workflow**: Intelligent routing system that analyzes user intent
- **Simple Chat Subgraph**: General conversation and simple tasks
- **Report Researcher Subgraph**: Research, analysis, and report writing assistance
- **Automatic Routing**: Based on keyword analysis and message complexity
- **Streaming Support**: Real-time response streaming to frontend

## File Structure

```
workflows/
├── __init__.py
├── README.md
├── supervisor_workflow.py      # Main supervisor that routes between workflows
├── simple_chat_subgraph.py     # Simple chat functionality
├── report_researcher_subgraph.py # Research and analysis functionality
└── chat_workflow.py            # Legacy chat workflow (for reference)
```

## Core Components

### 1. Supervisor Workflow (`supervisor_workflow.py`)

The intelligent orchestrator that analyzes user messages and routes them to the appropriate subgraph.

**Key Features:**

- **Intent Analysis**: Analyzes user messages to determine the most appropriate workflow
- **Intelligent Routing**: Routes between simple chat and report researcher based on content analysis
- **Confidence Scoring**: Provides confidence scores for routing decisions
- **Context Preservation**: Maintains conversation history and context across interactions
- **Error Handling**: Comprehensive error management and fallback mechanisms

**Routing Logic:**

- **Report Researcher**: Triggered by keywords like "report", "analysis", "research", "study", "SWOT", "market analysis", etc.
- **Simple Chat**: Triggered by general conversation keywords like "hello", "calculate", "explain", "what time", etc.
- **Default**: Falls back to simple chat for ambiguous cases

**State Schema:**

```python
class SupervisorState(TypedDict):
    message: str
    user_id: Optional[str]
    thread_id: Optional[str]
    conversation_history: Optional[List[dict]]
    response: str
    workflow_used: str  # "simple_chat" or "report_researcher"
    confidence_score: float
    timestamp: str
    error: bool
    error_message: Optional[str]
    analysis_type: Optional[str]
    messages: List[BaseMessage]
    routing_decision: Optional[str]
    routing_reason: Optional[str]
    conversation_context: Optional[dict]
```

### 2. Simple Chat Subgraph (`simple_chat_subgraph.py`)

Handles general conversation and simple tasks.

**Features:**

- General Q&A and conversation
- Simple mathematical calculations
- Current time queries
- Tool integration for enhanced functionality
- Context-aware responses

**Available Tools:**

- `get_current_time()`: Returns current date and time
- `calculate_simple_math(expression)`: Safely evaluates mathematical expressions

### 3. Report Researcher Subgraph (`report_researcher_subgraph.py`)

Specialized workflow for research, analysis, and report writing assistance.

**Features:**

- **Multi-Phase Workflow**: Analysis → Research → Writing → Reviewing
- **Analysis Types**: General, Market, Technical analysis
- **Structured Outlines**: Creates comprehensive report outlines
- **Source Suggestions**: Recommends research sources and databases
- **Data Analysis**: Uses frameworks like SWOT, PEST, 5 Forces
- **Report Formatting**: Professional report section formatting

**Available Tools:**

- `create_report_outline(topic, analysis_type, requirements)`: Creates structured report outlines
- `suggest_research_sources(topic, analysis_type)`: Recommends research sources
- `analyze_data_patterns(data_description, analysis_framework)`: Analyzes data using frameworks
- `format_report_section(section_title, content, section_type)`: Formats report sections

**Analysis Types:**

1. **General**: Standard research reports and analysis
2. **Market**: Market analysis, business analysis, competitive analysis
3. **Technical**: Technical analysis, system analysis, implementation studies

**Research Phases:**

1. **Analysis**: Topic definition, outline creation, framework selection
2. **Research**: Source gathering, data collection, information evaluation
3. **Writing**: Section drafting, content creation, report writing
4. **Reviewing**: Structure checking, editing, quality assurance

## API Integration

### Chat Routes (`routes/chat_routes.py`)

The chat routes have been updated to use the supervisor workflow:

**Endpoints:**

- `POST /api/chat` - Regular chat endpoint (non-streaming)
- `POST /api/chat/stream` - Streaming chat endpoint (Server-Sent Events)

**Request Format:**

```json
{
  "thread_id": "thread-uuid",
  "content": "User message here",
  "message_type": "text",
  "metadata": {
    "user_id": "optional-user-id"
  }
}
```

**Response Format:**

```json
{
  "message_id": "message-uuid",
  "thread_id": "thread-uuid",
  "content": "User message",
  "is_user": true,
  "message_type": "text",
  "created_at": "2024-01-01T12:00:00",
  "ai_response": "AI response text",
  "metadata": {
    "workflow_used": "simple_chat" | "report_researcher",
    "confidence_score": 0.85,
    "analysis_type": "market" | "technical" | "general" | null
  }
}
```

### Streaming Response Format

The streaming endpoint uses Server-Sent Events (SSE) with the following chunk types:

**Metadata Chunks:**

```json
{
  "type": "metadata",
  "data": {
    "node": "intent_analysis",
    "status": "analyzing_intent",
    "routing_decision": "report_researcher",
    "confidence_score": 0.85
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

**Content Chunks:**

```json
{
  "type": "content",
  "data": {
    "content": "Partial response text",
    "is_partial": true
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

**Error Chunks:**

```json
{
  "type": "error",
  "data": {
    "error": true,
    "error_message": "Error description"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

## Usage Examples

### Simple Chat Examples

```bash
# General conversation
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "thread-uuid",
    "content": "Hello, how are you today?",
    "message_type": "text"
  }'

# Mathematical calculation
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "thread-uuid",
    "content": "Calculate 25 * 4 + 10",
    "message_type": "text"
  }'
```

### Report Research Examples

```bash
# Market analysis request
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "thread-uuid",
    "content": "Help me create a market analysis report for the electric vehicle industry",
    "message_type": "text"
  }'

# SWOT analysis request
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "thread-uuid",
    "content": "Perform a SWOT analysis for a new tech startup",
    "message_type": "text"
  }'
```

### Streaming Examples

```bash
# Stream responses
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "thread-uuid",
    "content": "Create a comprehensive business plan outline",
    "message_type": "text"
  }'
```

## Routing Examples

### Messages that route to Simple Chat:

- "Hello, how are you?"
- "What time is it?"
- "Calculate 15 + 27"
- "Tell me a joke"
- "Explain quantum computing"
- "What's the weather like?"

### Messages that route to Report Researcher:

- "Create a market analysis report"
- "Help me with a SWOT analysis"
- "Write a business plan outline"
- "Research the competitive landscape"
- "Analyze industry trends"
- "Create a technical feasibility study"

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for OpenAI integration
- Database configuration for conversation persistence

### Model Configuration

- **Supervisor**: `gpt-4o-mini`, temperature 0.3 (focused routing decisions)
- **Simple Chat**: `gpt-4o-mini`, temperature 0.7 (conversational)
- **Report Researcher**: `gpt-4o-mini`, temperature 0.3 (analytical)

## Error Handling

The system includes comprehensive error handling:

- **Workflow Level**: Catches and handles errors in each workflow node
- **Routing Level**: Fallback to simple chat for routing errors
- **API Level**: Provides meaningful error messages to clients
- **Streaming Level**: Sends error chunks for real-time error reporting

## Performance Considerations

- **Intelligent Routing**: Reduces unnecessary processing by routing to appropriate workflows
- **Context Management**: Efficient conversation history management
- **Streaming**: Real-time response streaming for better UX
- **Tool Integration**: Tools are called only when needed
- **Caching**: Consider implementing response caching for repeated queries

## Extending the System

### Adding New Workflows

1. Create a new subgraph file (e.g., `new_workflow_subgraph.py`)
2. Implement the required state schemas and workflow logic
3. Add routing logic to the supervisor workflow
4. Update the intent analysis tool with new keywords

### Customizing Routing

1. Modify the `analyze_message_intent` tool in `supervisor_workflow.py`
2. Add new keywords to the routing logic
3. Adjust confidence scoring algorithms
4. Update the routing decision logic

### Adding New Tools

1. Define tools using the `@tool` decorator in the appropriate subgraph
2. Bind tools to the LLM instance
3. Handle tool calls in the workflow nodes
4. Update the system prompts to mention new capabilities

## Testing

To test the supervisor workflow system:

1. Start the chat-be server
2. Create a thread using the thread API
3. Send messages to `/api/chat` or `/api/chat/stream` endpoints
4. Observe the routing decisions in the response metadata
5. Test both simple chat and report researcher workflows

## Dependencies

- `langgraph`: Workflow orchestration and routing
- `langchain`: LLM integration and tools
- `langchain-openai`: OpenAI integration
- `fastapi`: API framework
- `pydantic`: Data validation
- `sqlalchemy`: Database operations

## Future Enhancements

- **Learning Routing**: Machine learning-based routing improvements
- **Multi-modal Support**: Image and document processing
- **Advanced Analytics**: Usage tracking and routing performance metrics
- **Custom Workflows**: User-defined workflow creation
- **Integration APIs**: Third-party service integrations
- **Advanced Caching**: Intelligent response caching strategies
