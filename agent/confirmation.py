from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_BASE_URL, AZURE_OPENAI_MODEL


class ConfirmationDecision(BaseModel):
    decision: Literal["approve", "reject", "other"]


class Confirmation:
    def __init__(self):
        self._llm = ChatOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            base_url=AZURE_OPENAI_BASE_URL,
            model=AZURE_OPENAI_MODEL,
            temperature=0.0,
        ).with_structured_output(ConfirmationDecision)

    async def invoke(self, user_input: str) -> ConfirmationDecision:
        prompt = """
        Determine whether the user's response approves or rejects a pending action.
        
        Return:
        - approve: the user clearly agrees to execute the action.
        - reject: the user clearly refuses or cancels the action.
        - other: the user does neither, including asking another 
        question, making another request, or requesting changes.
        """

        return await self._llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_input)
        ])
