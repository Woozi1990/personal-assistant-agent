from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class ToolSelection(BaseModel):
    tools: list[str] = Field(
        description=(
            "Names of all tools that may be required to fully complete "
            "the user's latest request, including prerequisite tools "
            "and tools that provide required inputs to other tools."
        )
    )


class ToolSelector:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm.with_structured_output(ToolSelection)

    def select(self, messages: list, tools: list) -> list[str]:
        tool_descriptions = "\n\n".join(
            f"""
                Tool: {tool.name}
        
                Description:
                {tool.description}
        
                Arguments:
                {tool.args}
            """
            for tool in tools
        )

        conversation = "\n".join(
            f"{message.type}: {message.content}"
            for message in messages[-6:]
        )

        # language=TEXT
        prompt = f"""
        Select all tools that may be required to fully complete the user's latest request.
        
        Available tools:
        {tool_descriptions}
        
        Recent conversation:
        {conversation}
        
        Selection procedure:

        1. Identify the actions the user wants to complete.
        
        2. Select the tools that directly perform those actions.
        
        3. For every selected tool, inspect its required arguments.
        
        4. If a required argument is not explicitly available from the conversation,
           do not invent the value. Include a tool that can retrieve or produce it.
        
        5. Repeat this dependency check until all required arguments for all selected
           tools can be obtained from either:
           - the conversation, or
           - another selected tool.
        
        6. If the user requests a completed action, include all tools needed to complete
           it, not only tools that prepare it.
        
        7. Never invent email addresses, phone numbers, IDs, or other missing identifiers.
        
        Return the complete tool set.
        """

        result = self.llm.invoke(prompt)
        return result.tools
