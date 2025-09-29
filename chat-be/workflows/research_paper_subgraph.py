from typing import TypedDict, List, Literal, Annotated, Optional, Dict, Any
from operator import add
from datetime import datetime
import json

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langchain_core.tools import tool


class ResearchPaperInputState(TypedDict):
    message: str
    conversation_history: List[dict]
    research_context: Optional[Dict[str, Any]]


class ResearchPaperOutputState(TypedDict):
    response: str
    research_context: Dict[str, Any]
    current_step: str
    paper_sections: Optional[Dict[str, str]]


class ResearchPaperState(ResearchPaperInputState, ResearchPaperOutputState):
    messages: Annotated[List[BaseMessage], add]
    topic: Optional[str]
    research_phase: str  # "planning", "research", "writing", "reviewing"
    outline: Optional[Dict[str, List[str]]]
    sources: List[str]
    current_section: Optional[str]


@tool
def create_research_outline(topic: str, requirements: str = ""):
    """Create a structured outline for a research paper"""
    return f"""
    Research Paper Outline for: {topic}
    
    I. Introduction
    - Background and context
    - Problem statement
    - Research objectives
    - Thesis statement
    
    II. Literature Review
    - Previous research
    - Theoretical framework
    - Research gaps
    
    III. Methodology
    - Research design
    - Data collection methods
    - Analysis approach
    
    IV. Results/Findings
    - Data presentation
    - Key findings
    - Analysis
    
    V. Discussion
    - Interpretation of results
    - Implications
    - Limitations
    
    VI. Conclusion
    - Summary of findings
    - Recommendations
    - Future research directions
    
    Requirements: {requirements}
    """


@tool
def suggest_research_sources(topic: str, section: str = ""):
    """Suggest research sources and databases for a given topic"""
    sources = {
        "general": [
            "Google Scholar",
            "PubMed (for medical/health topics)",
            "IEEE Xplore (for technical topics)",
            "JSTOR (for humanities/social sciences)",
            "ScienceDirect",
            "ResearchGate"
        ],
        "academic": [
            "University library databases",
            "Academic journals in the field",
            "Conference proceedings",
            "Dissertations and theses"
        ],
        "web": [
            "Government websites (.gov)",
            "Educational institutions (.edu)",
            "Professional organizations",
            "Reputable news sources"
        ]
    }
    
    if section:
        return f"For {section} of your research on {topic}, consider these sources: {', '.join(sources['general'] + sources['academic'])}"
    else:
        return f"For research on {topic}, here are recommended sources: {', '.join(sources['general'])}"


@tool
def format_citation(author: str, title: str, year: str, source: str, citation_style: str = "APA"):
    """Format a citation in the specified style"""
    if citation_style.upper() == "APA":
        return f"{author} ({year}). {title}. {source}."
    elif citation_style.upper() == "MLA":
        return f"{author}. \"{title}.\" {source}, {year}."
    else:
        return f"{author} ({year}). {title}. {source}."


@tool
def check_paper_structure(sections: Dict[str, str]):
    """Check if the research paper has proper structure and completeness"""
    required_sections = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
    present_sections = [section.lower() for section in sections.keys()]
    
    missing_sections = [section for section in required_sections if section not in present_sections]
    
    if not missing_sections:
        return "Paper structure is complete with all required sections."
    else:
        return f"Missing sections: {', '.join(missing_sections)}. Consider adding these to complete your paper."


def create_research_paper_subgraph():
    """Create a research paper writing subgraph"""
    
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)  # Lower temperature for more focused writing
    
    # Tools for research paper writing
    tools = [create_research_outline, suggest_research_sources, format_citation, check_paper_structure]
    llm_with_tools = llm.bind_tools(tools)
    
    async def initialize_research_context(state: ResearchPaperState) -> ResearchPaperState:
        """Initialize the research context and determine the current phase"""
        try:
            # Initialize messages if not present
            if "messages" not in state:
                state["messages"] = []
            
            # Initialize research context if not present
            if not state.get("research_context"):
                state["research_context"] = {
                    "topic": None,
                    "phase": "planning",
                    "outline": None,
                    "sections": {},
                    "sources": [],
                    "requirements": ""
                }
            
            # Extract topic from message if not already set
            if not state["research_context"].get("topic"):
                # Simple topic extraction - in a real implementation, you might use NLP
                message_lower = state["message"].lower()
                if any(keyword in message_lower for keyword in ["research", "paper", "thesis", "study"]):
                    # Extract potential topic (simplified)
                    words = state["message"].split()
                    topic_words = []
                    for i, word in enumerate(words):
                        if word.lower() in ["about", "on", "regarding", "concerning"]:
                            topic_words = words[i+1:i+5]  # Take next few words as topic
                            break
                    state["research_context"]["topic"] = " ".join(topic_words) if topic_words else "General Research Topic"
            
            # Determine research phase based on message content
            message_lower = state["message"].lower()
            if any(keyword in message_lower for keyword in ["outline", "structure", "plan"]):
                state["research_phase"] = "planning"
            elif any(keyword in message_lower for keyword in ["write", "draft", "section"]):
                state["research_phase"] = "writing"
            elif any(keyword in message_lower for keyword in ["review", "edit", "revise"]):
                state["research_phase"] = "reviewing"
            else:
                state["research_phase"] = "research"
            
            state["current_step"] = "context_initialized"
            
        except Exception as e:
            state["response"] = f"Error initializing research context: {str(e)}"
            state["current_step"] = "error"
            
        return state

    async def plan_research_phase(state: ResearchPaperState) -> ResearchPaperState:
        """Handle the planning phase of research paper writing"""
        try:
            system_message = SystemMessage(content="""
            You are a research paper writing assistant specializing in the planning phase. Help users:
            - Define research topics and questions
            - Create structured outlines
            - Identify research objectives
            - Plan methodology
            - Suggest research sources
            
            Be thorough and academic in your approach. Ask clarifying questions when needed.
            """)
            
            if not state["messages"]:
                state["messages"].append(system_message)
            
            human_message = HumanMessage(content=state["message"])
            state["messages"].append(human_message)
            
            response = await llm_with_tools.ainvoke(state["messages"])
            
            # Handle tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "create_research_outline":
                        topic = state["research_context"].get("topic", "Research Topic")
                        outline = create_research_outline(topic, state["research_context"].get("requirements", ""))
                        tool_results.append(f"Outline created: {outline}")
                        state["research_context"]["outline"] = outline
                    elif tool_call["name"] == "suggest_research_sources":
                        topic = state["research_context"].get("topic", "Research Topic")
                        sources = suggest_research_sources(topic)
                        tool_results.append(f"Sources suggested: {sources}")
                        state["research_context"]["sources"].append(sources)
                
                state["response"] = response.content + "\n\n" + "\n".join(tool_results)
            else:
                state["response"] = response.content
            
            state["current_step"] = "planning_completed"
            
        except Exception as e:
            state["response"] = f"Error in planning phase: {str(e)}"
            state["current_step"] = "error"
            
        return state

    async def research_phase(state: ResearchPaperState) -> ResearchPaperState:
        """Handle the research phase"""
        try:
            system_message = SystemMessage(content="""
            You are a research assistant helping with information gathering and source evaluation. Help users:
            - Find relevant sources
            - Evaluate source credibility
            - Organize research findings
            - Identify key themes and arguments
            - Suggest research gaps
            
            Focus on academic rigor and source quality.
            """)
            
            if not state["messages"]:
                state["messages"].append(system_message)
            
            human_message = HumanMessage(content=state["message"])
            state["messages"].append(human_message)
            
            response = await llm_with_tools.ainvoke(state["messages"])
            
            # Handle tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "suggest_research_sources":
                        topic = state["research_context"].get("topic", "Research Topic")
                        section = tool_call.get("args", {}).get("section", "")
                        sources = suggest_research_sources(topic, section)
                        tool_results.append(f"Sources: {sources}")
                        state["research_context"]["sources"].append(sources)
                
                state["response"] = response.content + "\n\n" + "\n".join(tool_results)
            else:
                state["response"] = response.content
            
            state["current_step"] = "research_completed"
            
        except Exception as e:
            state["response"] = f"Error in research phase: {str(e)}"
            state["current_step"] = "error"
            
        return state

    async def writing_phase(state: ResearchPaperState) -> ResearchPaperState:
        """Handle the writing phase"""
        try:
            system_message = SystemMessage(content="""
            You are a research paper writing assistant specializing in academic writing. Help users:
            - Write clear, well-structured sections
            - Maintain academic tone and style
            - Ensure proper citations and references
            - Develop coherent arguments
            - Maintain logical flow between sections
            
            Write in a formal, academic style with proper structure and citations.
            """)
            
            if not state["messages"]:
                state["messages"].append(system_message)
            
            human_message = HumanMessage(content=state["message"])
            state["messages"].append(human_message)
            
            response = await llm_with_tools.ainvoke(state["messages"])
            
            # Handle tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "format_citation":
                        args = tool_call.get("args", {})
                        citation = format_citation(
                            args.get("author", ""),
                            args.get("title", ""),
                            args.get("year", ""),
                            args.get("source", ""),
                            args.get("citation_style", "APA")
                        )
                        tool_results.append(f"Citation: {citation}")
                
                state["response"] = response.content + "\n\n" + "\n".join(tool_results)
            else:
                state["response"] = response.content
            
            state["current_step"] = "writing_completed"
            
        except Exception as e:
            state["response"] = f"Error in writing phase: {str(e)}"
            state["current_step"] = "error"
            
        return state

    async def review_phase(state: ResearchPaperState) -> ResearchPaperState:
        """Handle the review and editing phase"""
        try:
            system_message = SystemMessage(content="""
            You are a research paper review assistant. Help users:
            - Review paper structure and organization
            - Check for clarity and coherence
            - Identify areas for improvement
            - Ensure proper citations and formatting
            - Suggest revisions and edits
            
            Focus on improving the overall quality and academic rigor of the paper.
            """)
            
            if not state["messages"]:
                state["messages"].append(system_message)
            
            human_message = HumanMessage(content=state["message"])
            state["messages"].append(human_message)
            
            response = await llm_with_tools.ainvoke(state["messages"])
            
            # Handle tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "check_paper_structure":
                        sections = state["research_context"].get("sections", {})
                        structure_check = check_paper_structure(sections)
                        tool_results.append(f"Structure check: {structure_check}")
                
                state["response"] = response.content + "\n\n" + "\n".join(tool_results)
            else:
                state["response"] = response.content
            
            state["current_step"] = "review_completed"
            
        except Exception as e:
            state["response"] = f"Error in review phase: {str(e)}"
            state["current_step"] = "error"
            
        return state

    def phase_router(state: ResearchPaperState) -> Literal["plan_research_phase", "research_phase", "writing_phase", "review_phase"]:
        """Route to the appropriate phase handler"""
        phase = state.get("research_phase", "research")
        
        if phase == "planning":
            return "plan_research_phase"
        elif phase == "research":
            return "research_phase"
        elif phase == "writing":
            return "writing_phase"
        elif phase == "reviewing":
            return "review_phase"
        else:
            return "research_phase"  # Default to research phase

    # Create the graph
    graph = StateGraph(
        state_schema=ResearchPaperState,
        input_schema=ResearchPaperInputState,
        output_schema=ResearchPaperOutputState
    )
    
    # Add nodes
    graph.add_node("initialize_research_context", initialize_research_context)
    graph.add_node("plan_research_phase", plan_research_phase)
    graph.add_node("research_phase", research_phase)
    graph.add_node("writing_phase", writing_phase)
    graph.add_node("review_phase", review_phase)
    
    # Add edges
    graph.add_edge(START, "initialize_research_context")
    graph.add_conditional_edges(
        "initialize_research_context",
        phase_router,
        {
            "plan_research_phase": "plan_research_phase",
            "research_phase": "research_phase",
            "writing_phase": "writing_phase",
            "review_phase": "review_phase"
        }
    )
    graph.add_edge("plan_research_phase", END)
    graph.add_edge("research_phase", END)
    graph.add_edge("writing_phase", END)
    graph.add_edge("review_phase", END)
    
    return graph.compile()


def create_research_paper_agent():
    """Alternative factory function for creating a research paper agent"""
    return create_research_paper_subgraph()
