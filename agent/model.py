from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool

from agent.prompt import build_system_prompt
from agent.state import AgentState


class Model:
    def __init__(self, llm:BaseChatModel, tools:list[BaseTool]):
        self._llm = llm.bind_tools(tools)

    def invoke(self, state:AgentState):
        messages = [
            SystemMessage(content=build_system_prompt()),
            *state["messages"]
        ]

        response = self._llm.invoke(messages)

        return {
            "messages":[response]
        }