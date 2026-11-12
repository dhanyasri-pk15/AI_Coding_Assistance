from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from src.utils.logger import get_logger

logger = get_logger(__name__) 
class Pep8Client:
 
    PEP8_URL = "http://127.0.0.1:8002/mcp"
 
    def __init__(self):
        self.client = None
        self.tools = None
        self.logger = logger 
 
    async def connect(self):
        """
        Establish connection to Context7 MCP server
        """
        if self.client is None:
 
            self.logger.info(f"Connecting to pep8 MCP")
 
            self.client = MultiServerMCPClient({
                "context7": {
                    "transport": "streamable_http",
                    "url": self.PEP8_URL,
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
 
        self.logger.info("Fetching PEP8 MCP tools")
 
        self.tools = await self.client.get_tools()
 
        self.logger.info(f"Loaded {len(self.tools)} MCP tools")
 
        return self.tools
 
 
 