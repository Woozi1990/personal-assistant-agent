from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from agent.build_tools import build_tools
from agent.confirmation import ConfirmationHandler
from agent.graph import build_graph
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_MODEL, AZURE_OPENAI_BASE_URL


class Agent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            base_url=AZURE_OPENAI_BASE_URL,
            model=AZURE_OPENAI_MODEL,
            temperature=0.2,
        )
        self.checkpointer = InMemorySaver()

        self.confirmation_handler = ConfirmationHandler(self.llm)

        self.tools = build_tools()

        self.graph = build_graph(
            llm=self.llm,
            tools=self.tools,
            checkpointer=self.checkpointer,
            confirmation_handler = self.confirmation_handler
        )