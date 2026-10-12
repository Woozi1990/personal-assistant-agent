import asyncio
import uuid

from services.assistant_service import AssistantService


async def main():
    assistant = AssistantService()
    thread_id = str(uuid.uuid4())

    print("Personal Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input in {"exit", "quit"}:
            break

        response = await assistant.chat(user_input, thread_id)
        print(f"Assistant: {response['message']}")


if __name__ == '__main__':
    asyncio.run(main())
