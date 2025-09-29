from typing import TypedDict, List, Literal, Annotated
from operator import add
from datetime import datetime
import logging

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langchain_core.tools import tool

# Set up logging
logger = logging.getLogger(__name__)


def handle_workflow_error(state: dict, error: Exception, phase: str) -> dict:
    """Standardized error handling for workflow states"""
    error_message = f"Error in {phase}: {str(error)}"
    logger.error(error_message, exc_info=True)
    
    state["response"] = f"I encountered an error while processing your request. Please try again or rephrase your question."
    state["response_generated"] = True
    state["conversation_updated"] = False
    state["error"] = True
    state["error_message"] = error_message
    
    return state


class SimpleChatInputState(TypedDict):
    message: str
    conversation_history: List[dict]


class SimpleChatOutputState(TypedDict):
    response: str
    conversation_updated: bool


class SimpleChatState(SimpleChatInputState, SimpleChatOutputState):
    messages: Annotated[List[BaseMessage], add]
    context: str
    response_generated: bool


@tool
def get_current_time():
    """Get the current date and time"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate_simple_math(expression: str):
    """Calculate simple mathematical expressions safely"""
    try:
        # Only allow basic math operations for safety
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic mathematical operations are allowed"
        
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


def create_simple_chat_subgraph():
    """Create a simple chat subgraph for general conversation"""
    
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # Tools for simple chat
    tools = [get_current_time, calculate_simple_math]
    llm_with_tools = llm.bind_tools(tools)
    
    async def initialize_conversation(state: SimpleChatState) -> SimpleChatState:
        """Initialize the conversation with system message and context"""
        try:
            # Create system message
            system_message = SystemMessage(content="""
            You are a helpful AI assistant for general conversation. You can:
            - Answer questions and provide information
            - Help with simple calculations
            - Provide the current time
            - Engage in friendly conversation
            - Help with general tasks and questions
            
            Be helpful, accurate, and conversational. If you don't know something, 
            say so honestly. Keep responses concise but informative.
            """)
            
            # Initialize messages list
            if "messages" not in state:
                state["messages"] = []
            
            # Add system message if this is the first interaction
            if not state["messages"]:
                state["messages"].append(system_message)
            
            # Add conversation history as context
            if state.get("conversation_history"):
                context_parts = []
                for msg in state["conversation_history"][-5:]:  # Last 5 messages for context
                    role = "User" if msg["role"] == "user" else "Assistant"
                    context_parts.append(f"{role}: {msg['content']}")
                
                state["context"] = "\n".join(context_parts)
            else:
                state["context"] = ""
            
            state["response_generated"] = False
            
        except Exception as e:
            state = handle_workflow_error(state, e, "initialize_conversation")
            
        return state

    async def generate_response(state: SimpleChatState) -> SimpleChatState:
        """Generate a response using the LLM"""
        try:
            # Create a fresh messages list for this conversation turn
            messages = []
            
            # Add system message first
            system_message = SystemMessage(content="""
            You are a helpful AI assistant for general conversation. You can:
            - Answer questions and provide information
            - Help with simple calculations
            - Provide the current time
            - Engage in friendly conversation
            - Help with general tasks and questions
            
            Be helpful, accurate, and conversational. If you don't know something, 
            say so honestly. Keep responses concise but informative.
            """)
            messages.append(system_message)
            
            # Add conversation history to messages if available
            if state.get("conversation_history"):
                # Add conversation history as previous messages
                for msg in state["conversation_history"][-10:]:  # Last 10 messages for context
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
            
            # Create human message for current input
            human_message = HumanMessage(content=state["message"])
            messages.append(human_message)
            
            # Generate response using the fresh messages list
            response = await llm_with_tools.ainvoke(messages)
            
            # Handle tool calls if any
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tools and get results
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call.get("args", {})
                    
                    # Execute the appropriate tool
                    if tool_name == "get_current_time":
                        result = get_current_time()
                        tool_results.append(f"Current time: {result}")
                    elif tool_name == "calculate_simple_math":
                        expression = tool_args.get("expression", "")
                        result = calculate_simple_math(expression)
                        tool_results.append(result)
                    else:
                        tool_results.append(f"Tool {tool_name} executed with args: {tool_args}")
                
                # Combine LLM response with tool results
                llm_content = response.content or ""
                tool_content = "\n".join(tool_results)
                state["response"] = f"{llm_content}\n\n{tool_content}".strip()
            else:
                state["response"] = response.content
            
            state["response_generated"] = True
            state["conversation_updated"] = True
            
        except Exception as e:
            state = handle_workflow_error(state, e, "generate_response")
            
        return state

    async def finalize_response(state: SimpleChatState) -> SimpleChatState:
        """Finalize the response and ensure all fields are set"""
        try:
            if not state.get("response"):
                state["response"] = "I'm sorry, I couldn't generate a response."
            
            if "conversation_updated" not in state:
                state["conversation_updated"] = True
                
        except Exception as e:
            state = handle_workflow_error(state, e, "finalize_response")
            
        return state

    def should_continue(state: SimpleChatState) -> Literal["generate_response", "finalize_response"]:
        """Determine the next step in the workflow"""
        if state.get("response_generated", False):
            return "finalize_response"
        else:
            return "generate_response"

    # Create the graph
    graph = StateGraph(
        state_schema=SimpleChatState,
        input_schema=SimpleChatInputState,
        output_schema=SimpleChatOutputState
    )
    
    # Add nodes
    graph.add_node("initialize_conversation", initialize_conversation)
    graph.add_node("generate_response", generate_response)
    graph.add_node("finalize_response", finalize_response)
    
    # Add edges
    graph.add_edge(START, "initialize_conversation")
    graph.add_conditional_edges(
        "initialize_conversation",
        should_continue,
        {
            "generate_response": "generate_response",
            "finalize_response": "finalize_response"
        }
    )
    graph.add_edge("generate_response", "finalize_response")
    graph.add_edge("finalize_response", END)
    
    return graph.compile()


class SimpleChatWorkflow:
    """Wrapper class to handle threadID configuration for simple chat subgraph"""
    
    def __init__(self):
        self.subgraph = create_simple_chat_subgraph()
    
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
    
    async def astream(self, input_data: dict, config: dict = None, **kwargs):
        """Stream the simple chat subgraph with threadID configuration"""
        # Ensure config is properly structured
        if config is None:
            config = {}
        if 'configurable' not in config:
            config['configurable'] = {}
        
        # Add threadID to config if provided in input_data
        if 'thread_id' in input_data and input_data['thread_id']:
            config['configurable']['thread_id'] = input_data['thread_id']
        
        kwargs['config'] = config
        async for chunk in self.subgraph.astream(input_data, **kwargs):
            yield chunk


def create_simple_chat_agent():
    """Alternative factory function for creating a simple chat agent"""
    return SimpleChatWorkflow()
