from typing import Any
from .client import AvairaClient

class AvairaBlockedError(Exception):
    pass

class AvairaCrewAITool:
    def __init__(self, wrapped_tool: Any, avaira: AvairaClient):
        self.wrapped_tool = wrapped_tool
        self.avaira = avaira
        self.name = wrapped_tool.name
        self.description = wrapped_tool.description

    def run(self, *args: Any, **kwargs: Any) -> Any:
        # Simplified validation call
        import asyncio
        intent = {
            "action": self.name,
            "parameters": {"args": args, "kwargs": kwargs},
            "estimated_value": 0.0
        }
        loop = asyncio.get_event_loop()
        validation = loop.run_until_complete(self.avaira.validate(intent))

        if not validation["approved"]:
            raise AvairaBlockedError(f"Avaira blocked: {validation['violations']}")

        return self.wrapped_tool.run(*args, **kwargs)

def protect_crew(crew: Any, avaira_client: AvairaClient):
    for agent in crew.agents:
        protected_tools = [
            AvairaCrewAITool(wrapped_tool=t, avaira=avaira_client)
            for t in agent.tools
        ]
        agent.tools = protected_tools
    return crew
