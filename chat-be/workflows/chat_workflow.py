from typing import TypedDict, Literal, List, Optional, Annotated
from operator import add
import asyncio
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from .simple_chat_subgraph import create_simple_chat_subgraph
from .research_paper_subgraph import create_research_paper_subgraph


class ChatInputState(TypedDict):
    message: str
    chat_type: str  # "simple" or "research_paper"
    user_id: Optional[str]
    thread_id: Optional[str]


class ChatOutputState(TypedDict):
    response: str
    chat_type: str
    timestamp: str
    error: bool
    error_message: Optional[str]


class ChatState(ChatInputState, ChatOutputState):
    messages: Annotated[List[BaseMessage], add]
    conversation_history: List[dict]
    research_context: Optional[dict]
    current_step: Optional[str]


class ChatWorkflow:
    def __init__(self, llm_model="gpt-4o-mini", temperature=0.7):
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.simple_chat_subgraph = create_simple_chat_subgraph()
        self.research_paper_subgraph = create_research_paper_subgraph()
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        workflow = StateGraph(
            ChatState, 
            input=ChatInputState, 
            output=ChatOutputState
        )
        
        # Add nodes
        workflow.add_node("route_chat_type", self.route_chat_type)
        workflow.add_node("simple_chat", self.simple_chat_node)
        workflow.add_node("research_paper_chat", self.research_paper_node)
        workflow.add_node("format_response", self.format_response_node)
        workflow.add_node("error_handler", self.error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("route_chat_type")
        
        # Add edges
        workflow.add_conditional_edges(
            "route_chat_type",
            self.chat_type_router,
            {
                "simple": "simple_chat",
                "research_paper": "research_paper_chat",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("simple_chat", "format_response")
        workflow.add_edge("research_paper_chat", "format_response")
        workflow.add_edge("error_handler", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()

    async def route_chat_type(self, state: ChatState) -> ChatState:
        """Route the chat based on type and initialize conversation state"""
        try:
            # Initialize messages if not present
            if "messages" not in state:
                state["messages"] = []
            
            # Add user message to conversation
            user_message = HumanMessage(content=state["message"])
            state["messages"].append(user_message)
            
            # Initialize conversation history if not present
            if "conversation_history" not in state:
                state["conversation_history"] = []
            
            # Add to conversation history
            state["conversation_history"].append({
                "role": "user",
                "content": state["message"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Set timestamp
            state["timestamp"] = datetime.now().isoformat()
            state["error"] = False
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in routing: {str(e)}"
            
        return state

    def chat_type_router(self, state: ChatState) -> Literal["simple", "research_paper", "error"]:
        """Route to appropriate chat subgraph based on chat_type"""
        if state.get("error", False):
            return "error"
        
        chat_type = state.get("chat_type", "simple").lower()
        
        if chat_type == "research_paper":
            return "research_paper"
        elif chat_type == "simple":
            return "simple"
        else:
            return "error"

    async def simple_chat_node(self, state: ChatState) -> ChatState:
        """Handle simple chat using the simple chat subgraph"""
        try:
            # Prepare input for simple chat subgraph
            simple_input = {
                "message": state["message"],
                "conversation_history": state.get("conversation_history", [])
            }
            
            # Invoke simple chat subgraph
            result = await self.simple_chat_subgraph.ainvoke(simple_input)
            
            # Extract response
            state["response"] = result.get("response", "I'm sorry, I couldn't process your request.")
            state["current_step"] = "simple_chat_completed"
            
            # Add AI response to conversation history
            state["conversation_history"].append({
                "role": "assistant",
                "content": state["response"],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in simple chat: {str(e)}"
            state["response"] = "I encountered an error while processing your message."
            
        return state

    async def research_paper_node(self, state: ChatState) -> ChatState:
        """Handle research paper writing using the research paper subgraph"""
        try:
            # Prepare input for research paper subgraph
            research_input = {
                "message": state["message"],
                "conversation_history": state.get("conversation_history", []),
                "research_context": state.get("research_context", {})
            }
            
            # Invoke research paper subgraph
            result = await self.research_paper_subgraph.ainvoke(research_input)
            
            # Extract response and update context
            state["response"] = result.get("response", "I'm sorry, I couldn't help with your research paper.")
            state["research_context"] = result.get("research_context", {})
            state["current_step"] = result.get("current_step", "research_completed")
            
            # Add AI response to conversation history
            state["conversation_history"].append({
                "role": "assistant",
                "content": state["response"],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in research paper chat: {str(e)}"
            state["response"] = "I encountered an error while helping with your research paper."
            
        return state

    async def error_handler_node(self, state: ChatState) -> ChatState:
        """Handle errors in the chat workflow"""
        error_message = state.get("error_message", "An unknown error occurred")
        state["response"] = f"I'm sorry, but I encountered an error: {error_message}"
        state["current_step"] = "error_handled"
        
        # Add error response to conversation history
        state["conversation_history"].append({
            "role": "assistant",
            "content": state["response"],
            "timestamp": datetime.now().isoformat()
        })
        
        return state

    async def format_response_node(self, state: ChatState) -> ChatState:
        """Format the final response"""
        try:
            # Ensure all required fields are present
            if "response" not in state:
                state["response"] = "No response generated"
            
            if "timestamp" not in state:
                state["timestamp"] = datetime.now().isoformat()
            
            if "error" not in state:
                state["error"] = False
                
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error formatting response: {str(e)}"
            state["response"] = "Error formatting response"
            
        return state

    async def ainvoke(self, input_data: dict, **kwargs):
        """Invoke the chat workflow"""
        return await self.workflow.ainvoke(input_data, **kwargs)

    async def astream(self, input_data: dict, **kwargs):
        """Stream the chat workflow for real-time responses"""
        async for chunk in self.workflow.astream(input_data, **kwargs):
            yield chunk


def create_chat_workflow(llm_model="gpt-4o-mini", temperature=0.7):
    """Factory function to create a chat workflow instance"""
    return ChatWorkflow(llm_model=llm_model, temperature=temperature)
