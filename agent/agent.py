from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from agent.build_tools import build_tools
from agent.executor import Executor
from agent.graph import AgentGraph
from agent.model import Model

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
        self._model = Model(
            llm=self._llm,
            tools=self._tools,
        )
        self._executor = Executor(
            tools=self._tools,
        )
        self._checkpointer = InMemorySaver()

        self._graph = AgentGraph(
            model=self._model,
            executor=self._executor,
        ).build(checkpointer=self._checkpointer)

    async def invoke(
            self,
            user_input: str,
            thread_id:str = "default"
    ):
        result = await self._graph.ainvoke(
            {
                "messages":
                    HumanMessage(content=user_input)
            },
            config={
                "configurable":{
                    "thread_id": thread_id
                }
            }
        )

        final_message = result["messages"][-1]
        return final_message.content
