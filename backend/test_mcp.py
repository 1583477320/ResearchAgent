import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    client = MultiServerMCPClient({
        "scholar": {
            "command": "python",
            "args": ["-m", "scholar_search_mcp"],
            "transport": "stdio",
        }
    })
    
    tools = await client.get_tools()
    print("Available tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

if __name__ == "__main__":
    asyncio.run(main())
