# Copyright (c) Microsoft. All rights reserved.


import asyncio

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

# This concept sample shows how to use the OpenAI connector to create a
# chat experience with a local model running in LM studio: https://lmstudio.ai/
# Please follow the instructions here: https://lmstudio.ai/docs/local-server to set up LM studio.
# The default model used in this sample is phi3 due to its compact size.

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = Kernel()

service_id = "local-gpt"

openAIClient: AsyncOpenAI = AsyncOpenAI(
    api_key="fake-key",  # This cannot be an empty string, use a fake key
    base_url="http://localhost:1234/v1",
)
kernel.add_service(OpenAIChatCompletion(service_id=service_id, 
                                        ai_model_id="deepseek-r1-distill-qwen-14b", 
                                        async_client=openAIClient))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
settings.max_tokens = 2000
settings.temperature = 0.7
settings.top_p = 0.8

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)

chat_history = ChatHistory(system_message=system_message)
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need")


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    # Activar streaming en settings
    settings.stream = True
    answer_stream = kernel.invoke_stream(chat_function, KernelArguments(user_input=user_input, chat_history=chat_history))
    chat_history.add_user_message(user_input)
    print("Mosscap:> ", end="", flush=True)
    last_chunk = ""
    async for chunk in answer_stream:
        # Si el chunk es una lista, recorre cada elemento
        chunks = chunk if isinstance(chunk, list) else [chunk]
        for c in chunks:
            # Si tiene 'items', busca los StreamingTextContent y extrae el texto
            if hasattr(c, 'items') and c.items:
                for item in c.items:
                    text = getattr(item, 'text', None)
                    if text:
                        print(text, end="", flush=True)
                        last_chunk += text
            else:
                # Si no, intenta imprimir el contenido como string
                print(str(c), end="", flush=True)
                last_chunk += str(c)
    chat_history.add_assistant_message(last_chunk)
    print()
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())