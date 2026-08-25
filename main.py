import asyncio
import traceback

from langchain_core.messages import HumanMessage

from agent.agent import Agent


async def main():
    agent = Agent()

    print("Personal Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input in {"exit", "quit"}:
            break

        try:

            response = await agent.invoke(user_input)

            print(f"Assistant: {response}")
        except Exception as e:
            traceback.print_exc()



if __name__ == '__main__':
    asyncio.run(main())
