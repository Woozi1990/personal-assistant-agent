import json

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from agent.state import AgentState


class Executor:
    def __init__(self, tools: list[BaseTool]):
        self._tools = {
            tool.name: tool
            for tool in tools
        }

    def invoke(self, state: AgentState) -> dict:
        last_message = state["messages"][-1]

        if not isinstance(last_message, AIMessage):
            return {"messages": []}

        tool_messages: list[ToolMessage] = []

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            arguments = tool_call["args"]
            tool_call_id = tool_call["id"]

            tool = self._tools.get(tool_name)

            print(f"Tool: {tool_name}")
            print(f"Arguments: {arguments}")

            if tool is None:
                result = {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found."
                }
            else:
                try:
                    result = tool.invoke(arguments)

                    print(f"Result: {result}")
                except Exception as e:
                    result = {
                        "success": False,
                        "error": str(e)
                    }
            tool_messages.append(
                ToolMessage(
                    content=self._serialize(result),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

        return {
            "messages": tool_messages,

        }

    @staticmethod
    def _serialize(result):
        if isinstance(result, str):
            return result
        if hasattr(result, "model_dump"):
            result = result.model_dump(mode="json")

        return json.dumps(
            result,
            ensure_ascii=False,
            default=str
        )
