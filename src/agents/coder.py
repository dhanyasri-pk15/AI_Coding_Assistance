import asyncio
from langgraph.prebuilt import create_react_agent
from src.agents.prompts import coder_prompt
from mcp_clients.pep8 import Pep8Client
from src.utils.logger import get_logger
from src.utils.helpers import extract_text

logger = get_logger(__name__) 
pep8 = Pep8Client()
class CoderAgent:
    def __init__(self):
        self.agent = None
        self.llm = None
        self.tools = None
        self.logger = logger
#1.37 - 1.51 create agent for coder
    async def create_agent(self, service):
 
        self.logger.info(f"Creating coder agent")
        try:
            self.llm =  service.get_llm()
            self.tools = await pep8.get_tools()
            self.agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=coder_prompt
            )
        except Exception as e:
            self.logger.error(f"Tool agent creation failed. Using LLM fallback: {e}")
            self.agent = None
 
        return self

# 1.89 - 1.98 invoke coder agent 
    async def invoke_agent(self, state):
 
        self.logger.info("Running coder node")
 
        message = state["message"]
        research = state.get("research_data", "")
 
        query = f"""
User Request:
{message}
 
Research Context:
{research}
 
Generate production-ready Python code.
Follow PEP8 standards.
Use FastAPI if API related.
"""
 
        code = None
        try:
            if self.agent:
                result = await self.agent.ainvoke({
                    "messages": [{"role": "user", "content": query}]
                })
                code = extract_text(result["messages"][-1].content)
            else:
                result = await self.llm.ainvoke(query)
                code = extract_text(result.content)
        except Exception as e:
            err_str = str(e)
            self.logger.warning(f"Coder agent error: {err_str} - trying direct LLM fallback")

            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                code = f"Error: Gemini API quota exceeded (429). Please wait or upgrade your plan."
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                # Try direct LLM fallback once
                try:
                    result = await self.llm.ainvoke(query)
                    code = extract_text(result.content)
                except Exception:
                    code = f"Error: Gemini API is temporarily experiencing high demand (503). Please try again in a few moments."
            else:
                try:
                    result = await self.llm.ainvoke(query)
                    code = extract_text(result.content)
                except Exception as retry_err:
                    self.logger.error(f"LLM fallback also failed: {retry_err}")
                    code = f"Error: Code generation failed: {retry_err}"
 
        return {
            "code": code,
            "step": state["step"] + 1
        }
