from typing import List, Dict, Any
import asyncio
import json
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScholarSearchClient:
    def __init__(self):
        self.client = None
        self.tool = None
    
    async def _ensure_client(self):
        if self.client is None:
            self.client = MultiServerMCPClient({
                "scholar": {
                    "command": "python",
                    "args": ["-m", "scholar_search_mcp"],
                    "transport": "stdio",
                }
            })
            tools = await self.client.get_tools()
            self.tool = next((t for t in tools if t.name == "search_papers"), None)
            if self.tool:
                logger.info(f"Loaded MCP tool via MultiServerMCPClient: {self.tool.name}")
    
    async def search(self, query: str, max_results: int = 10, venues: list = None,
                     year: str = None) -> Dict[str, Any]:
        await self._ensure_client()

        if not self.tool:
            raise ValueError("search_papers tool not found in MCP server")

        params = {"query": query, "limit": max_results}
        if venues:
            params["venue"] = venues
        if year:
            params["year"] = year

        result = await self.tool.ainvoke(params)
        
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse result as JSON: {result}")
                return {"papers": []}
        
        if isinstance(result, dict):
            if "papers" in result:
                return result
            elif "data" in result:
                return {"papers": result["data"]}
        
        return {"papers": []}


_scholar_client = None


def get_scholar_search_client() -> ScholarSearchClient:
    global _scholar_client
    if _scholar_client is None:
        _scholar_client = ScholarSearchClient()
    return _scholar_client
