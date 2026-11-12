from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from src.utils.logger import get_logger

logger = get_logger(__name__) 
 
class Context7Client:
 
    CONTEXT7_URL = "https://mcp.context7.com/mcp"
 
    def __init__(self, api_key: str | None =None):
        self.api_key = api_key or os.getenv("CONTEXT7_API_KEY")
        self.client = None
        self.tools = None
        self.logger = logger

    async def connect(self):
        """
        Establish connection to Context7 MCP server
        """
        if self.client is None:

            if not self.api_key:
                self.logger.warning("CONTEXT7_API_KEY is not set. Skipping Context7 MCP connection.")
                self.tools = []
                return

            self.logger.info(f"Connecting to Context7 MCP")

            headers = {}
            if self.api_key:
                headers["CONTEXT7_API_KEY"] = str(self.api_key)

            self.client = MultiServerMCPClient({
                "context7": {
                    "transport": "streamable_http",
                    "url": self.CONTEXT7_URL,
                    "headers": headers
                }
            })
 
    async def get_tools(self):
        """
        Fetch MCP tools from Context7.
        Tools are cached after first load.
        """
 
        # ensure connection exists
        if self.client is None:
            await self.connect()
 
        # return cached tools if already loaded
        if self.tools is not None:
            return self.tools
 
        self.logger.info(f"Fetching Context7 MCP tools")
 
        self.tools = await self.client.get_tools()
 
        self.logger.info(f"Loaded {len(self.tools)} MCP tools")
 
        return self.tools
 
 
 