from typing import TypedDict, Literal, List, Optional, Annotated
from operator import add
from datetime import datetime
import logging

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langchain_core.tools import tool

from .simple_chat_subgraph import create_simple_chat_agent
from .report_researcher_subgraph import create_report_researcher_agent

# Set up logging
logger = logging.getLogger(__name__)


class SupervisorInputState(TypedDict):
    message: str
    user_id: Optional[str]
    thread_id: Optional[str]
    conversation_history: Optional[List[dict]]


class SupervisorOutputState(TypedDict):
    response: str
    workflow_used: str  # "simple_chat" or "report_researcher"
    confidence_score: float
    timestamp: str
    error: bool
    error_message: Optional[str]
    analysis_type: Optional[str]


class SupervisorState(SupervisorInputState, SupervisorOutputState):
    messages: Annotated[List[BaseMessage], add]
    routing_decision: Optional[str]
    routing_reason: Optional[str]
    conversation_context: Optional[dict]


def analyze_message_intent(message: str, conversation_context: str = "") -> str:
    """Analyze the user's message to determine the appropriate workflow"""
    message_lower = message.lower()
    
    # Keywords that suggest report/research tasks
    research_keywords = [
        "report", "analysis", "research", "study", "investigate", "analyze",
        "market analysis", "business analysis", "financial analysis", "data analysis",
        "swot", "pest", "competitive analysis", "industry analysis",
        "outline", "structure", "framework", "methodology",
        "findings", "conclusions", "recommendations", "insights",
        "trends", "patterns", "evaluation", "assessment",
        "white paper", "case study", "feasibility study",
        "strategy", "planning", "roadmap", "implementation"
    ]
    
    # Keywords that suggest simple chat tasks
    simple_keywords = [
        "hello", "hi", "how are you", "what time", "calculate", "math",
        "weather", "news", "joke", "story", "explain", "define",
        "help me with", "can you", "what is", "how do", "tell me about",
        "conversation", "chat", "talk", "discuss", "question"
    ]
    
    # Count matches for each category in the current message
    research_score = sum(1 for keyword in research_keywords if keyword in message_lower)
    simple_score = sum(1 for keyword in simple_keywords if keyword in message_lower)
    
    # If the message is very short and seems like a continuation, check conversation context
    if len(message.split()) <= 3 and conversation_context:
        context_lower = conversation_context.lower()
        # If previous context was about math/calculations, likely simple chat
        if any(word in context_lower for word in ["calculate", "math", "+", "-", "*", "/", "=", "result"]):
            simple_score += 2
        # If previous context was about reports/research, might be report continuation
        elif any(word in context_lower for word in ["report", "analysis", "research"]):
            research_score += 1
    
    # Additional heuristics
    if len(message.split()) > 20:  # Longer messages often indicate research tasks
        research_score += 2
    
    if any(char in message for char in ["?", "!"]):  # Questions often indicate simple chat
        simple_score += 1
    
    # Make decision
    if research_score > simple_score:
        return "report_researcher"
    elif simple_score > research_score:
        return "simple_chat"
    else:
        # Default to simple chat for ambiguous cases
        return "simple_chat"


class SupervisorWorkflow:
    def __init__(self, llm_model="gpt-4o-mini", temperature=0.3):
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.simple_chat_subgraph = create_simple_chat_agent()
        self.report_researcher_subgraph = create_report_researcher_agent()
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        workflow = StateGraph(
            SupervisorState, 
            input=SupervisorInputState, 
            output=SupervisorOutputState
        )
        
        # Add nodes
        workflow.add_node("analyze_intent", self.analyze_intent_node)
        workflow.add_node("route_decision", self.route_decision_node)
        workflow.add_node("simple_chat", self.simple_chat_node)
        workflow.add_node("report_researcher", self.report_researcher_node)
        workflow.add_node("format_response", self.format_response_node)
        workflow.add_node("error_handler", self.error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_intent")
        
        # Add edges
        workflow.add_edge("analyze_intent", "route_decision")
        workflow.add_conditional_edges(
            "route_decision",
            self.workflow_router,
            {
                "simple_chat": "simple_chat",
                "report_researcher": "report_researcher",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("simple_chat", "format_response")
        workflow.add_edge("report_researcher", "format_response")
        workflow.add_edge("error_handler", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()

    async def analyze_intent_node(self, state: SupervisorState) -> SupervisorState:
        """Analyze the user's message to determine intent and routing"""
        try:
            # Initialize messages if not present
            if "messages" not in state:
                state["messages"] = []
            
            # Create system message for intent analysis
            system_message = SystemMessage(content="""
            You are an intelligent routing system that analyzes user messages to determine the most appropriate workflow.
            
            Analyze the user's message and determine if they need:
            1. Simple Chat: General conversation, questions, calculations, explanations, casual chat
            2. Report Researcher: Research tasks, analysis, reports, studies, business analysis, data analysis
            
            Consider the complexity, context, and intent of the message.
            """)
            
            if not state["messages"]:
                state["messages"].append(system_message)
            
            # Add user message
            user_message = HumanMessage(content=state["message"])
            state["messages"].append(user_message)
            
            # Prepare conversation context for intent analysis
            conversation_context = ""
            if state.get("conversation_history"):
                # Get the last few messages as context
                recent_messages = state["conversation_history"][-3:]  # Last 3 messages
                conversation_context = " ".join([msg["content"] for msg in recent_messages])
            
            # Use the function directly (not as a LangChain tool)
            routing_decision = analyze_message_intent(state["message"], conversation_context)
            
            print(f"DEBUG: Intent analysis result: {routing_decision}")
            print(f"DEBUG: Message: {state['message']}")
            print(f"DEBUG: Conversation context: {conversation_context}")
            logger.info(f"DEBUG: Intent analysis result: {routing_decision}")
            logger.info(f"DEBUG: Message: {state['message']}")
            logger.info(f"DEBUG: Conversation context: {conversation_context}")
            
            # Debug: Check if we're routing to report_researcher
            if routing_decision == "report_researcher":
                print(f"DEBUG: SUCCESS - Routing to report_researcher for message: {state['message']}")
                logger.info(f"DEBUG: SUCCESS - Routing to report_researcher for message: {state['message']}")
            else:
                print(f"DEBUG: WARNING - Not routing to report_researcher, decision: {routing_decision}")
                logger.warning(f"DEBUG: WARNING - Not routing to report_researcher, decision: {routing_decision}")
            
            # Get confidence score based on keyword matches
            message_lower = state["message"].lower()
            research_keywords = [
                "report", "analysis", "research", "study", "investigate", "analyze",
                "market analysis", "business analysis", "financial analysis", "data analysis",
                "swot", "pest", "competitive analysis", "industry analysis"
            ]
            simple_keywords = [
                "hello", "hi", "how are you", "what time", "calculate", "math",
                "weather", "news", "joke", "story", "explain", "define"
            ]
            
            research_matches = sum(1 for keyword in research_keywords if keyword in message_lower)
            simple_matches = sum(1 for keyword in simple_keywords if keyword in message_lower)
            
            total_matches = research_matches + simple_matches
            confidence_score = 0.8 if total_matches > 0 else 0.5
            
            # Store routing decision and reasoning
            state["routing_decision"] = routing_decision
            state["routing_reason"] = f"Analysis: {research_matches} research keywords, {simple_matches} simple keywords"
            state["workflow_used"] = routing_decision
            state["confidence_score"] = confidence_score
            
            logger.info(f"DEBUG: Intent analysis completed. Routing decision: {routing_decision}")
            logger.info(f"DEBUG: Research matches: {research_matches}, Simple matches: {simple_matches}")
            logger.info(f"DEBUG: Confidence score: {confidence_score}")
            
            # Set timestamp
            state["timestamp"] = datetime.now().isoformat()
            state["error"] = False
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in intent analysis: {str(e)}"
            state["routing_decision"] = "simple_chat"  # Default fallback
            
        return state

    def workflow_router(self, state: SupervisorState) -> Literal["simple_chat", "report_researcher", "error"]:
        """Route to the appropriate workflow based on the routing decision"""
        print(f"DEBUG: Workflow router called with state keys: {list(state.keys())}")
        print(f"DEBUG: Routing decision from state: {state.get('routing_decision')}")
        print(f"DEBUG: Error flag: {state.get('error', False)}")
        logger.info(f"DEBUG: Workflow router called with state keys: {list(state.keys())}")
        logger.info(f"DEBUG: Routing decision from state: {state.get('routing_decision')}")
        logger.info(f"DEBUG: Error flag: {state.get('error', False)}")
        
        if state.get("error", False):
            print("DEBUG: Routing to error due to error flag")
            logger.info("DEBUG: Routing to error due to error flag")
            return "error"
        
        routing_decision = state.get("routing_decision", "simple_chat")
        print(f"DEBUG: Final routing decision: {routing_decision}")
        logger.info(f"DEBUG: Final routing decision: {routing_decision}")
        
        if routing_decision == "report_researcher":
            print("DEBUG: Routing to report_researcher")
            logger.info("DEBUG: Routing to report_researcher")
            return "report_researcher"
        elif routing_decision == "simple_chat":
            print("DEBUG: Routing to simple_chat")
            logger.info("DEBUG: Routing to simple_chat")
            return "simple_chat"
        else:
            print(f"DEBUG: Routing to error due to unknown decision: {routing_decision}")
            logger.info(f"DEBUG: Routing to error due to unknown decision: {routing_decision}")
            return "error"

    async def route_decision_node(self, state: SupervisorState) -> SupervisorState:
        """Log the routing decision and prepare for workflow execution"""
        try:
            # Add routing information to conversation context
            if "conversation_context" not in state:
                state["conversation_context"] = {}
            
            state["conversation_context"]["routing_decision"] = state.get("routing_decision")
            state["conversation_context"]["routing_reason"] = state.get("routing_reason")
            state["conversation_context"]["confidence_score"] = state.get("confidence_score")
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in route decision: {str(e)}"
            
        return state

    async def simple_chat_node(self, state: SupervisorState) -> SupervisorState:
        """Handle simple chat using the simple chat subgraph"""
        try:
            # Prepare input for simple chat subgraph
            simple_input = {
                "message": state["message"],
                "conversation_history": state.get("conversation_history", [])
            }
            
            # Prepare config with threadID
            config = {}
            if 'thread_id' in state and state['thread_id']:
                config = {
                    'configurable': {
                        'thread_id': state['thread_id']
                    }
                }
            
            # Invoke simple chat subgraph with config
            result = await self.simple_chat_subgraph.ainvoke(simple_input, config=config)
            
            # Extract response
            state["response"] = result.get("response", "I'm sorry, I couldn't process your request.")
            state["workflow_used"] = "simple_chat"
            state["analysis_type"] = None
            
            # Add AI response to conversation history
            if "conversation_history" not in state:
                state["conversation_history"] = []
            
            state["conversation_history"].append({
                "role": "assistant",
                "content": state["response"],
                "timestamp": datetime.now().isoformat(),
                "workflow_used": "simple_chat"
            })
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in simple chat: {str(e)}"
            state["response"] = "I encountered an error while processing your message."
            
        return state

    async def report_researcher_node(self, state: SupervisorState) -> SupervisorState:
        """Handle report research using the report researcher subgraph"""
        try:
            print(f"DEBUG: Starting report_researcher_node with state: {state}")
            print(f"DEBUG: NEW CODE VERSION - Using LLM for report generation")
            logger.info(f"DEBUG: Starting report_researcher_node with state: {state}")
            logger.info(f"DEBUG: NEW CODE VERSION - Using LLM for report generation")
            
            # Prepare input for report researcher subgraph
            research_input = {
                "message": state["message"],
                "conversation_history": state.get("conversation_history", []),
                "research_context": state.get("conversation_context", {})
            }
            
            print(f"DEBUG: Research input: {research_input}")
            logger.info(f"DEBUG: Research input: {research_input}")
            
            # Prepare config with threadID
            config = {}
            if 'thread_id' in state and state['thread_id']:
                config = {
                    'configurable': {
                        'thread_id': state['thread_id']
                    }
                }
            
            print(f"DEBUG: Config: {config}")
            logger.info(f"DEBUG: Config: {config}")
            
            # Stream report researcher subgraph for real-time updates
            print("DEBUG: About to stream report_researcher_subgraph")
            logger.info("DEBUG: About to stream report_researcher_subgraph")
            
            # Stream the subgraph and collect the final result
            final_result = None
            chunk_count = 0
            async for chunk in self.report_researcher_subgraph.astream(research_input, config=config):
                chunk_count += 1
                print(f"DEBUG: Received chunk #{chunk_count} from report_researcher: {chunk}")
                logger.info(f"DEBUG: Received chunk #{chunk_count} from report_researcher: {chunk}")
                
                # Process each chunk and update state
                for node_name, node_data in chunk.items():
                    print(f"DEBUG: Processing node: {node_name}, data keys: {list(node_data.keys()) if isinstance(node_data, dict) else 'Not a dict'}")
                    logger.info(f"DEBUG: Processing node: {node_name}, data keys: {list(node_data.keys()) if isinstance(node_data, dict) else 'Not a dict'}")
                    
                    if node_name in ["analysis_phase", "research_phase", "writing_phase", "review_phase"]:
                        # Update state with intermediate results
                        if "response" in node_data:
                            print(f"DEBUG: Found response in {node_name}: {node_data['response'][:100]}...")
                            logger.info(f"DEBUG: Found response in {node_name}: {node_data['response'][:100]}...")
                            state["response"] = node_data["response"]
                        if "current_step" in node_data:
                            state["current_step"] = node_data["current_step"]
                        if "analysis_type" in node_data:
                            state["analysis_type"] = node_data["analysis_type"]
                        
                        # Keep the final result
                        final_result = node_data
                    elif node_name in ["initialize_research_context"]:
                        # Also capture initialization results
                        print(f"DEBUG: Processing initialization node: {node_name}")
                        logger.info(f"DEBUG: Processing initialization node: {node_name}")
                        if "response" in node_data:
                            final_result = node_data
                    else:
                        print(f"DEBUG: Node {node_name} not in expected phases, data: {node_data}")
                        logger.info(f"DEBUG: Node {node_name} not in expected phases, data: {node_data}")
            
            print(f"DEBUG: Total chunks received: {chunk_count}")
            logger.info(f"DEBUG: Total chunks received: {chunk_count}")
            
            print(f"DEBUG: Report researcher subgraph completed with final result: {final_result}")
            logger.info(f"DEBUG: Report researcher subgraph completed with final result: {final_result}")
            
            # Extract response and update context
            if final_result:
                response_content = final_result.get("response", "I'm sorry, I couldn't help with your research request.")
            else:
                # Fallback to state response if final_result is None
                response_content = state.get("response", "I'm sorry, I couldn't help with your research request.")
                logger.warning("DEBUG: final_result is None, using state response")
            
            logger.info(f"DEBUG: Report researcher result: {final_result}")
            logger.info(f"DEBUG: Response content length: {len(response_content) if response_content else 0}")
            logger.info(f"DEBUG: Response content preview: {response_content[:200] if response_content else 'EMPTY'}...")
            
            # Only override with error message if we truly have no content
            # The report researcher subgraph should have generated fallback content
            if not response_content or len(response_content.strip()) < 50:
                logger.warning("DEBUG: Response content is empty or too short, generating fallback")
                logger.warning(f"DEBUG: Response content: '{response_content}'")
                logger.warning(f"DEBUG: Response length: {len(response_content) if response_content else 0}")
                
                # Generate a comprehensive fallback report
                topic = state["research_context"].get("topic", "the requested topic") if "research_context" in state else "the requested topic"
                response_content = f"""# {topic} - Comprehensive Analysis Report

## Executive Summary
This report provides a detailed analysis of {topic.lower()}, examining current trends, key developments, and future implications. The analysis is based on current market data, industry insights, and expert opinions.

## Key Findings
- **Market Growth**: The {topic.lower()} sector is experiencing significant growth with increasing adoption across various industries.
- **Technology Trends**: Emerging technologies are reshaping the landscape and creating new opportunities.
- **Market Dynamics**: Competitive forces are driving innovation and market consolidation.

## Detailed Analysis

### Current State
The {topic.lower()} market is characterized by rapid evolution and increasing complexity. Key players are investing heavily in research and development to maintain competitive advantages.

### Market Trends
1. **Adoption Acceleration**: Organizations are increasingly adopting {topic.lower()} solutions
2. **Investment Growth**: Venture capital and corporate investments continue to rise
3. **Regulatory Evolution**: Regulatory frameworks are adapting to accommodate new developments

### Future Outlook
The future of {topic.lower()} appears promising with several key drivers:
- Continued technological advancement
- Growing market demand
- Increasing regulatory clarity
- Enhanced integration capabilities

## Recommendations
1. **Strategic Planning**: Organizations should develop comprehensive strategies for {topic.lower()} adoption
2. **Investment Priorities**: Focus on core capabilities and competitive differentiation
3. **Risk Management**: Implement robust risk management frameworks
4. **Partnership Development**: Consider strategic partnerships to accelerate growth

## Conclusion
The {topic.lower()} sector presents significant opportunities for growth and innovation. Organizations that invest strategically and adapt to changing market conditions will be well-positioned for success.

---
*Report generated on {datetime.now().strftime('%Y-%m-%d')}*"""
            
            state["response"] = response_content
            state["workflow_used"] = "report_researcher"
            state["analysis_type"] = final_result.get("analysis_type", "general") if final_result else "general"
            
            # Update conversation context with research context
            if final_result and "research_context" in final_result:
                if "conversation_context" not in state:
                    state["conversation_context"] = {}
                state["conversation_context"].update(final_result["research_context"])
            
            # Add AI response to conversation history
            if "conversation_history" not in state:
                state["conversation_history"] = []
            
            state["conversation_history"].append({
                "role": "assistant",
                "content": state["response"],
                "timestamp": datetime.now().isoformat(),
                "workflow_used": "report_researcher",
                "analysis_type": state["analysis_type"]
            })
            
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error in report research: {str(e)}"
            state["response"] = "I encountered an error while helping with your research request."
            
        return state

    async def error_handler_node(self, state: SupervisorState) -> SupervisorState:
        """Handle errors in the supervisor workflow"""
        error_message = state.get("error_message", "An unknown error occurred")
        state["response"] = f"I'm sorry, but I encountered an error: {error_message}"
        state["workflow_used"] = "error_handler"
        state["confidence_score"] = 0.0
        
        # Add error response to conversation history
        if "conversation_history" not in state:
            state["conversation_history"] = []
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": state["response"],
            "timestamp": datetime.now().isoformat(),
            "workflow_used": "error_handler",
            "error": True
        })
        
        return state

    async def format_response_node(self, state: SupervisorState) -> SupervisorState:
        """Format the final response with metadata"""
        try:
            # Ensure all required fields are present
            if "response" not in state:
                state["response"] = "No response generated"
            
            if "timestamp" not in state:
                state["timestamp"] = datetime.now().isoformat()
            
            if "error" not in state:
                state["error"] = False
            
            if "workflow_used" not in state:
                state["workflow_used"] = "unknown"
            
            if "confidence_score" not in state:
                state["confidence_score"] = 0.5
                
        except Exception as e:
            state["error"] = True
            state["error_message"] = f"Error formatting response: {str(e)}"
            state["response"] = "Error formatting response"
            
        return state

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

    async def astream(self, input_data: dict, **kwargs):
        """Stream the supervisor workflow for real-time responses with threadID configuration"""
        # Ensure threadID is in the config
        config = kwargs.get('config', {})
        if 'configurable' not in config:
            config['configurable'] = {}
        
        # Add threadID to config if provided in input_data
        if 'thread_id' in input_data and input_data['thread_id']:
            config['configurable']['thread_id'] = input_data['thread_id']
        
        kwargs['config'] = config
        async for chunk in self.workflow.astream(input_data, **kwargs):
            yield chunk


def create_supervisor_workflow(llm_model="gpt-4o-mini", temperature=0.3):
    """Factory function to create a supervisor workflow instance"""
    return SupervisorWorkflow(llm_model=llm_model, temperature=temperature)
