import asyncio
from avaira_shield.client import AvairaClient
from avaira_shield.config import AvairaConfig, RiskEnvelope
from avaira_shield.langchain_integration import protect_agent

# Mock tools since we don't have LangChain installed in the environment
class MockSearchTool:
    def __init__(self):
        self.name = "duckduckgo_search"
        self.description = "Search the web"
    def _run(self, query):
        return f"Results for {query}"
    def _arun(self, query):
        return self._run(query)

class MockAgentExecutor:
    def __init__(self, tools):
        self.tools = tools

async def main():
    envelope = RiskEnvelope(allowed_actions=["duckduckgo_search"])
    config = AvairaConfig(api_key="lang_key", risk_envelope=envelope, api_url="http://localhost:8000")
    client = AvairaClient(config)

    executor = MockAgentExecutor([MockSearchTool()])
    protected_executor = protect_agent(executor, client)

    print("Running protected LangChain tool...")
    tool = protected_executor.tools[0]
    try:
        res = tool._run("YC Demo Day 2024")
        print(f"Tool Result: {res}")
    except Exception as e:
        print(f"Tool Blocked: {e}")

if __name__ == "__main__":
    asyncio.run(main())
