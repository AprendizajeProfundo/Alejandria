import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from alejandria.domain.base_agent import BaseAgent
from alejandria.domain.agent_response import AgentResponse
from alejandria.agents.prompts import SOCIAL_SYSTEM_MESSAGE
import logging
import inspect
from autogen_agentchat.messages import ModelClientStreamingChunkEvent

load_dotenv()


class AutoGenSocialAgent(BaseAgent):
    name = "AutoGenSocialAgent"
    instructions = "Responde con conocimiento social y habilidades interpersonales."

    def __init__(self, api_key=None, model=None, system_message=None):
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        llm_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        social_prompt = system_message or os.getenv(
            "SOCIAL_SYSTEM_MESSAGE",
            SOCIAL_SYSTEM_MESSAGE,
        )
        self.model_client = OpenAIChatCompletionClient(
            model=llm_model, api_key=openai_api_key
        )
        self.assistant = AssistantAgent(
            name="SocialAssistant",
            model_client=self.model_client,
            system_message=social_prompt,
            model_client_stream=True,  # Habilita streaming real de tokens
        )

    async def act(self, req):
        try:
            response = await self.assistant.run(task=req.message)
            content = None
            if hasattr(response, "messages") and isinstance(response.messages, list):
                for msg in reversed(response.messages):
                    if (
                        hasattr(msg, "source")
                        and msg.source == self.assistant.name
                        and hasattr(msg, "content")
                        and msg.content
                    ):
                        content = msg.content
                        break
            elif isinstance(response, list):
                for msg in reversed(response):
                    if hasattr(msg, "content") and msg.content:
                        content = msg.content
                        break
            elif hasattr(response, "content") and response.content:
                content = response.content
            if not content:
                content = "[AutoGen] No se pudo extraer respuesta textual."
        except Exception as e:
            logging.error("[AutoGenSocialAgent] ERROR: %s", e)
            content = f"[AutoGen] Error: {e}"
        return AgentResponse(agent_name=self.name, content=content, meta={})

    async def act_stream(self, req, on_token):
        try:
            buffer = ""
            async for event in self.assistant.run_stream(task=req.message):
                if isinstance(event, ModelClientStreamingChunkEvent):
                    token = event.content
                    buffer += token
                    if on_token:
                        if inspect.iscoroutinefunction(on_token):
                            await on_token(token)
                        else:
                            on_token(token)
                elif hasattr(event, "content") and isinstance(getattr(event, "content", None), str):
                    buffer += event.content
            return AgentResponse(
                agent_name=self.name,
                content=buffer,
                meta={},
            )
        except Exception as e:
            if on_token:
                if inspect.iscoroutinefunction(on_token):
                    await on_token(f"[AutoGen] Error: {e}")
                else:
                    on_token(f"[AutoGen] Error: {e}")
            return AgentResponse(
                agent_name=self.name,
                content=f"[AutoGen] Error: {e}",
                meta={},
            )
