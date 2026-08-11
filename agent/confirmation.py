from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agent.pending_action import PendingAction


class PendingActionDecision(BaseModel):
    decision:Literal[
        "confirm",
        "modify",
        "cancel",
        "other"
    ] = Field(
        description=(
            "The user's decision about the pending action. "
            "confirm means the user clearly approves it; "
            "modify means the user wants to change it; "
            "cancel means the user rejects or cancels it; "
            "other means the intent is unrelated or unclear."
        )
    )

class ConfirmationHandler:
    def __init__(self, llm:ChatOpenAI):
        self.llm = llm.with_structured_output(PendingActionDecision)

    def classify(self, user_input:str, pending_action:PendingAction) -> PendingActionDecision:
        prompt = f"""
        There is an action waiting for user confirmation.

        Pending action:
        Action: {pending_action.action}
        Data: {pending_action.data}

        User response:
        {user_input}

        Determine the user's decision about the pending action.

        - confirm: The user clearly approves performing the pending action.
        - modify: The user wants to change the pending action before it is performed.
        - cancel: The user clearly rejects or cancels the pending action.
        - other: The user's response does not clearly indicate any of the above.

        Do not treat an ambiguous response as confirmation.
        """
        return self.llm.invoke(prompt)
