from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agent.build_tools import build_tools
from agent.confirmation import ConfirmationHandler
from agent.prompts import SYSTEM_PROMPT
from agent.session_state import SessionState
from agent.tool_selector import ToolSelector
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_MODEL, AZURE_OPENAI_BASE_URL


class Agent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            base_url=AZURE_OPENAI_BASE_URL,
            model=AZURE_OPENAI_MODEL,
            temperature=0.2,
        )

        self.state = SessionState()
        self.confirmation_handler = ConfirmationHandler(self.llm)

        self.tools = build_tools(self.state)

        self.tool_selector = ToolSelector(llm=self.llm)

    def build_agent(
            self,
            user_message: str,
            allowed_tool_names: list[str]
    ):
        if allowed_tool_names is not None:
            selected_names = allowed_tool_names
        else:
            selected_names = self.tool_selector.select(
                messages=user_message,
                tools=self.tools,
            )
            selected_names = [
                name for name in selected_names if name != "send_email"
            ]

        selected_tools = [
            tool for tool in self.tools if tool.name in selected_names
        ]

        print("Selected tools:", selected_names)

        return create_agent(
            model=self.llm,
            system_prompt=SYSTEM_PROMPT,
            tools=selected_tools,

        )

    def classify_pending_action(self, user_input):
        if self.state.pending_action is None:
            return None

        return self.confirmation_handler.classify(
            user_input,
            self.state.pending_action,
        )

    def clear_pending_action(self):
        self.state.pending_action = None

    def get_pending_action(self):
        return self.state.pending_action
