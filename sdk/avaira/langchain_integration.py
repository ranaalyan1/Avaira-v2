import asyncio
from typing import Any, Optional
try:
    from langchain_core.tools import BaseTool
except ImportError:
    class BaseTool: pass # Placeholder

from .client import AvairaClient

class AvairaBlockedError(Exception):
    pass

class AvairaProtectedTool(BaseTool):
    wrapped_tool: Any
    avaira: AvairaClient

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        intent = {
            "action": self.wrapped_tool.name,
            "parameters": {"args": args, "kwargs": kwargs},
            "estimated_value": 0.0
        }

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If loop is already running, we are likely in an async environment
            # but being called via a sync tool.
            import threading
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor() as executor:
                validation = executor.submit(lambda: asyncio.run(self.avaira.validate(intent))).result()
        else:
            validation = loop.run_until_complete(self.avaira.validate(intent))

        if not validation["approved"]:
            raise AvairaBlockedError(
                f"Avaira blocked: {validation['violations']}"
            )
        return self.wrapped_tool._run(*args, **kwargs)

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        intent = {
            "action": self.wrapped_tool.name,
            "parameters": {"args": args, "kwargs": kwargs},
            "estimated_value": 0.0
        }
        validation = await self.avaira.validate(intent)
        if not validation["approved"]:
            raise AvairaBlockedError(
                f"Avaira blocked: {validation['violations']}"
            )
        return await self.wrapped_tool._arun(*args, **kwargs)

def protect_agent(agent_executor: Any, avaira_client: AvairaClient):
    protected_tools = [
        AvairaProtectedTool(
            wrapped_tool=t,
            avaira=avaira_client,
            name=t.name,
            description=t.description
        )
        for t in agent_executor.tools
    ]
    agent_executor.tools = protected_tools
    return agent_executor
