from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from agent.build_tools import build_tools
from agent.middleware.tool_logging import tool_logging
from agent.prompt import dynamic_system_prompt

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_MODEL, AZURE_OPENAI_BASE_URL


class Agent:
    def __init__(self):
        self._llm = ChatOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            base_url=AZURE_OPENAI_BASE_URL,
            model=AZURE_OPENAI_MODEL,
            temperature=0.0,
        )
        self._tools = build_tools()
        self._checkpointer = InMemorySaver()

        self._agent = create_agent(
            model=self._llm,
            tools=self._tools,
            middleware=[
                dynamic_system_prompt,
                tool_logging,
            ],
            checkpointer=self._checkpointer,
        )

    def invoke(
            self,
            user_input: str,
            thread_id: str = "default"
    ):
        result = self._agent.invoke(
            {
                "messages":
                    [
                        HumanMessage(content=user_input)
                    ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        final_message = result["messages"][-1]
        return final_message.content
