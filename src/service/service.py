import os
import boto3
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_aws import ChatBedrock
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.models.state import AgentState
from src.agents.coder import CoderAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.researcher import ResearchAgent
from src.mcp_clients.context7 import Context7Client
from src.models.models import ChatResponse
from src.utils.logger import get_logger

load_dotenv()

coder = CoderAgent()
reviewer = ReviewerAgent()
researcher = ResearchAgent()

class GraphService:
 
    def __init__(self):
        self.graph = None
        self.tools = None
        self.llm = self.get_llm()
        self.checkpointer = None
        self.checkpointer_context = None
        self.coder = coder
        self.reviewer = reviewer
        self.researcher = researcher
        self.logger = get_logger(__name__) 
 
# 1.39 - 1.40 get_llm function
    def get_llm(self): 
        gemini_model = os.getenv("GEMINI_MODEL_ID")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        if gemini_model or google_api_key:
            import logging
            logging.getLogger("google_genai").setLevel(logging.ERROR)
            logging.getLogger("google_genai.models").setLevel(logging.ERROR)
            try:
                from google.genai.models import Models, AsyncModels
                Models._logged_afc_warning = True
                AsyncModels._logged_afc_warning = True
            except Exception:
                pass

            return ChatGoogleGenerativeAI(
                model=gemini_model or "gemini-3.5-flash",
                api_key=google_api_key,
                max_retries=2,
                timeout=30.0
            )

        bedrock_client = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
 
        return ChatBedrock(
            client=bedrock_client,
            model_id=os.getenv("BEDROCK_NOVA_MODEL_ID"),
            provider="amazon",
            model_kwargs={
                "max_tokens": 1000,
                "temperature": 0.7
            }
        )
 
# 1.127 - 1.132 define start router function to decide which agent to run first based on user intent
    def start_router(self, state: AgentState):
        msg = state["message"].lower()
 
        if "research" in msg and "code" in msg:
            return "research"
 
        if "research" in msg:
            return "research"
 
        if "review" in msg:
            return "reviewer"
        return "coder"

# 1.136 - 1.140 define reviewer_router function to track the approval status
    def reviewer_router(self, state: AgentState):
   
        approved = state.get("approved", False)
        step = state.get("step", 0)
       
        if step > 6:
            self.logger.info(f"Max steps reached - END")
            return "end"
       
        if approved:
            self.logger.info(f"Reviewer approved - END")
            return "end"
       
        self.logger.info(f"Reviewer rejected - Research")
        return "research"
 
# 1.37 - 1.147 performs compile function to compile graph
    async def compile(self):
 
        #print("Loading Context7 MCP tools")
        #context7= Context7Client(api_key=os.getenv("CONTEXT7_API_KEY"))
        #self.tools = await context7.get_tools()
 
        self.logger.info(f"Creating Agents")
 
        await self.coder.create_agent(self)
        await self.reviewer.create_agent(self)
        await self.researcher.create_agent(self)
 
        builder = StateGraph(AgentState)
 
        builder.add_node("coder", self.coder_node)
        builder.add_node("reviewer", self.reviewer_node)
        builder.add_node("research", self.research_node)
 
        builder.add_conditional_edges(
            START,
            self.start_router,
            {
                "coder": "coder",
                "reviewer": "reviewer",
                "research": "research"
            }
        )
        builder.add_edge("coder", "reviewer")
        builder.add_conditional_edges(
            "reviewer",
            self.reviewer_router,
            {
                "research": "research",
                "end": END
            }
        )
 
        builder.add_edge("research", "coder")
 
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "coder_agent")

        POSTGRES_CONN_STRING = os.getenv(
            "POSTGRES_CONN_STRING",
            f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}"
        )
 
        self.logger.info(f"Initializing Postgres Checkpointer")
 
        self.checkpointer_context = AsyncPostgresSaver.from_conn_string(
            POSTGRES_CONN_STRING
        )
 
        self.checkpointer = await self.checkpointer_context.__aenter__()
 
        await self.checkpointer.setup()
 
        self.graph = builder.compile(
            checkpointer=self.checkpointer
        )
 
        self.logger.info(f"LangGraph compiled successfully")

# 1.88 - 1.100 add a node named coder
    async def coder_node(self, state: AgentState):
 
        self.logger.info(f"Running coder node")
        self.logger.info(f"STATE: {state}")
 
        return await self.coder.invoke_agent(state)

# 1.101 - 1.114 add a node named reviewer
    async def reviewer_node(self, state: AgentState):
 
        self.logger.info(f"Running reviewer node")
        self.logger.info(f"STATE: {state}")
 
        return await self.reviewer.invoke_agent(state)
 
# 1.116 - 1.125 add a node named researcher
    async def research_node(self, state: AgentState):
 
        self.logger.info(f"Running research node")
        self.logger.info(f"STATE: {state}")
 
        return await self.researcher.invoke_agent(state)
 
# 1.166 - 1.177 invoke graph that is compiled using invoke function
    async def invoke(self, thread_id: str, message: str):
        try:
            if self.graph is None:
                await self.compile()
    
            self.logger.info(f"Invoking LangGraph")
    
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
    
            result = await self.graph.ainvoke(
                {
                    "thread_id": thread_id,
                    "message": message,
                    "code": None,
                    "research_data": None,
                    "review_feedback": None,
                    "approved": False,
                    "step": 0
                },
                config=config
            )
    
            return result
        
        except Exception as e:
            return ChatResponse(
                thread_id = thread_id,
                reply = str(e),
                code = None,
                review_feedback = None,
                research_data = None
            )
        

 
 
 