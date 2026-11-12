from langgraph.prebuilt import create_react_agent
from src.agents.prompts import research_prompt
from mcp_clients.context7 import Context7Client
from src.utils.logger import get_logger
from src.utils.helpers import extract_text

logger = get_logger(__name__) 
 
class ResearchAgent:
    def __init__(self):
        self.agent = None
        self.llm = None
        self.tools = None
        self.logger = logger
 
#1.70 - 1.85 create agent for researcher
    async def create_agent(self, service):
        self.logger.info("Creating research agent")
        try:
            self.llm = service.get_llm()
            context7=Context7Client()
            self.tools= await context7.get_tools()
            self.agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=research_prompt
            )
        except Exception as e:
            self.logger.error(f"Research tool agent failed. Using LLM fallback: {e}")
            self.agent = None
        return self

# 1.116 - 1.123 invoke researcher agent 
    async def invoke_agent(self, state):
 
        self.logger.info(f"Running research node")
 
        message = state.get("message", "")
        review_feedback = state.get("review_feedback", "")
        step = state.get("step", 0)

        # Edge case: Empty message
        if not message or not message.strip():
            self.logger.warning("Empty research query — returning default")
            return {
                "research_data": "No research topic provided. Using general Python best practices.",
                "step": step + 1
            }

        # Build a focused research query
        if review_feedback and step > 1:
            # Re-research mode: focus on reviewer's concerns
            query = f"""
The following code was REJECTED by a reviewer. Research solutions for the specific issues.

Original User Request:
{message}

Reviewer Feedback:
{review_feedback}

Focus your research on solving the reviewer's specific concerns.
Follow the STRICT OUTPUT FORMAT from your system prompt.
"""
        else:
            # Initial research mode
            query = f"""
Research the following topic to help a Python developer write production code.

User Request:
{message}

Follow the STRICT OUTPUT FORMAT from your system prompt.
Focus on practical implementation details, libraries, and code patterns.
"""

        try:
 
            if self.agent:
                result = await self.agent.ainvoke({
                    "messages": [{"role": "user", "content": query}]
                })
 
                research = extract_text(result["messages"][-1].content)
 
            else:
                result = await self.llm.ainvoke(query)
                research = extract_text(result.content)
 
        except Exception as e:
 
            self.logger.error(f"Research failed: {e}")

            # Rate limit / high demand handling
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "503" in str(e) or "UNAVAILABLE" in str(e):
                research = (
                    f"Research skipped due to temporary API high demand / rate limit. "
                    f"Coder should proceed with general best practices for: {message}"
                )
            else:
                research = f"Research failed: {str(e)}. Coder should use general knowledge."
 
        return {
            "research_data": research,
            "step": step + 1
        }
 
 
