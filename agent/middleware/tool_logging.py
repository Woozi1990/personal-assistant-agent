from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

class ToolCallingMiddleware(AgentMiddleware):

    async def awrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest], ToolMessage | Command]
    ) -> ToolMessage | Command:
        tool_call = request.tool_call

        print(f"Tool: {tool_call['name']}")
        print(f"Arguments: {tool_call['args']}")

        result = await handler(request)
        print(f"Result: {result}")
        return result
