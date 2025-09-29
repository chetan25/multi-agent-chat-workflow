# ThreadID Configuration Update

This document outlines the changes made to ensure all agent workflows run with a config that includes a threadID for proper conversation management and LangGraph checkpointing.

## Changes Made

### 1. Supervisor Workflow (`supervisor_workflow.py`)

**Updated Methods:**

- `ainvoke()`: Now automatically adds threadID to config from input_data
- `astream()`: Now automatically adds threadID to config from input_data
- `simple_chat_node()`: Passes threadID config to simple chat subgraph
- `report_researcher_node()`: Passes threadID config to report researcher subgraph

**Key Changes:**

```python
async def ainvoke(self, input_data: dict, **kwargs):
    """Invoke the supervisor workflow with threadID configuration"""
    # Ensure threadID is in the config
    config = kwargs.get('config', {})
    if 'configurable' not in config:
        config['configurable'] = {}

    # Add threadID to config if provided in input_data
    if 'thread_id' in input_data and input_data['thread_id']:
        config['configurable']['thread_id'] = input_data['thread_id']

    kwargs['config'] = config
    return await self.workflow.ainvoke(input_data, **kwargs)
```

### 2. Simple Chat Subgraph (`simple_chat_subgraph.py`)

**New Wrapper Class:**

- `SimpleChatWorkflow`: Wrapper class that handles threadID configuration
- Ensures threadID is properly passed to the underlying subgraph
- Maintains the same interface while adding config management

**Key Changes:**

```python
class SimpleChatWorkflow:
    """Wrapper class to handle threadID configuration for simple chat subgraph"""

    async def ainvoke(self, input_data: dict, config: dict = None, **kwargs):
        """Invoke the simple chat subgraph with threadID configuration"""
        # Ensure config is properly structured
        if config is None:
            config = {}
        if 'configurable' not in config:
            config['configurable'] = {}

        # Add threadID to config if provided in input_data
        if 'thread_id' in input_data and input_data['thread_id']:
            config['configurable']['thread_id'] = input_data['thread_id']

        kwargs['config'] = config
        return await self.subgraph.ainvoke(input_data, **kwargs)
```

### 3. Report Researcher Subgraph (`report_researcher_subgraph.py`)

**New Wrapper Class:**

- `ReportResearcherWorkflow`: Wrapper class that handles threadID configuration
- Ensures threadID is properly passed to the underlying subgraph
- Maintains the same interface while adding config management

**Key Changes:**

```python
class ReportResearcherWorkflow:
    """Wrapper class to handle threadID configuration for report researcher subgraph"""

    async def ainvoke(self, input_data: dict, config: dict = None, **kwargs):
        """Invoke the report researcher subgraph with threadID configuration"""
        # Ensure config is properly structured
        if config is None:
            config = {}
        if 'configurable' not in config:
            config['configurable'] = {}

        # Add threadID to config if provided in input_data
        if 'thread_id' in input_data and input_data['thread_id']:
            config['configurable']['thread_id'] = input_data['thread_id']

        kwargs['config'] = config
        return await self.subgraph.ainvoke(input_data, **kwargs)
```

### 4. Chat Routes (`routes/chat_routes.py`)

**Updated Endpoints:**

- `send_chat_message()`: Now passes threadID config to supervisor workflow
- `stream_chat_response()`: Now passes threadID config to supervisor workflow

**Key Changes:**

```python
# Prepare config with threadID for LangGraph checkpointing
config = {
    "configurable": {
        "thread_id": request.thread_id
    }
}

# Invoke supervisor workflow with config
result = await supervisor_workflow.ainvoke(workflow_input, config=config)
```

### 5. App Configuration (`app.py`)

**Updated Initialization:**

- Supervisor workflow now compiled with checkpointer for thread management
- Enables proper conversation state persistence

**Key Changes:**

```python
# Initialize supervisor workflow with checkpointer
supervisor_workflow = create_supervisor_workflow()
# Set checkpointer for thread management
supervisor_workflow.workflow = supervisor_workflow.workflow.compile(checkpointer=checkpointer)
# Store workflow in app state for access in routes
app.state.supervisor_workflow = supervisor_workflow
```

## Benefits

### 1. **Proper Thread Management**

- Each conversation thread maintains its own state
- LangGraph checkpointing works correctly
- Conversation context is preserved across interactions

### 2. **Config Consistency**

- All workflows now receive threadID in their config
- Consistent configuration structure across all agents
- Proper LangGraph config format maintained

### 3. **State Persistence**

- Conversation state is automatically saved and restored
- Enables proper conversation continuity
- Supports complex multi-turn interactions

### 4. **Error Handling**

- Graceful fallback when threadID is not provided
- Maintains backward compatibility
- Robust error handling throughout the chain

## Configuration Structure

All workflows now use the following config structure:

```python
config = {
    "configurable": {
        "thread_id": "thread-uuid-here"
    }
}
```

## Usage Examples

### Regular Chat

```python
workflow_input = {
    "message": "Hello, how are you?",
    "thread_id": "thread-123",
    "conversation_history": [...]
}

config = {
    "configurable": {
        "thread_id": "thread-123"
    }
}

result = await supervisor_workflow.ainvoke(workflow_input, config=config)
```

### Streaming Chat

```python
async for chunk in supervisor_workflow.astream(workflow_input, config=config):
    # Process streaming chunks
    pass
```

## Testing

To verify the threadID configuration is working:

1. **Check Config Passing**: Verify that threadID appears in workflow configs
2. **State Persistence**: Test that conversation state is maintained across messages
3. **Checkpointing**: Verify that LangGraph checkpointing works with threadID
4. **Error Handling**: Test behavior when threadID is missing or invalid

## Migration Notes

- **Backward Compatibility**: All existing functionality is preserved
- **No Breaking Changes**: Existing API endpoints continue to work
- **Enhanced Functionality**: New thread management capabilities added
- **Performance**: Minimal performance impact, improved state management

## Future Enhancements

- **Thread Analytics**: Track conversation patterns per thread
- **Thread Cleanup**: Automatic cleanup of old conversation threads
- **Thread Sharing**: Support for shared conversation threads
- **Advanced State Management**: More sophisticated state persistence strategies
