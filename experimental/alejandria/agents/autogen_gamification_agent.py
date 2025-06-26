import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from alejandria.domain.base_agent import BaseAgent
from alejandria.domain.agent_response import AgentResponse
from alejandria.agents.prompts import GAMIFICATION_SYSTEM_MESSAGE
import logging
import asyncio
import inspect

load_dotenv()


class AutoGenGamificationAgent(BaseAgent):
    name = "AutoGenGamificationAgent"
    instructions = "Responde con dinámicas de gamificación y motivación."

    def __init__(self, api_key=None, model=None, system_message=None):
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        llm_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        gamification_prompt = system_message or os.getenv(
            "GAMIFICATION_SYSTEM_MESSAGE",
            GAMIFICATION_SYSTEM_MESSAGE,
        )
        logging.warning(
            f"[AutoGenGamificationAgent] Inicializando con modelo: "
            f"{llm_model}, API key: {openai_api_key[:8]}... (oculta)"
        )
        self.model_client = OpenAIChatCompletionClient(
            model=llm_model, api_key=openai_api_key
        )
        self.assistant = AssistantAgent(
            name="GamificationAssistant",
            model_client=self.model_client,
            system_message=gamification_prompt,
        )

    async def act(self, req):
        try:
            response = await self.assistant.run(task=req.message)
            content = None
            # Si la respuesta tiene 'messages', buscar el último mensaje del
            # asistente con 'content'
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
            logging.error("[AutoGenGamificationAgent] ERROR: %s", e)
            content = f"[AutoGen] Error: {e}"
        return AgentResponse(agent_name=self.name, content=content, meta={})

    async def act_stream(self, req, on_token):
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
            for token in content.split():
                await asyncio.sleep(0.01)
                if on_token and inspect.iscoroutinefunction(on_token):
                    await on_token(token + " ")
                elif on_token:
                    on_token(token + " ")
            return AgentResponse(agent_name=self.name, content=content, meta={})
        except Exception as e:
            logging.error("[AutoGenGamificationAgent] ERROR: %s", e)
            if on_token and inspect.iscoroutinefunction(on_token):
                await on_token(f"[AutoGen] Error: {e}")
            elif on_token:
                on_token(f"[AutoGen] Error: {e}")
            return AgentResponse(
                agent_name=self.name,
                content=f"[AutoGen] Error: {e}",
                meta={},
            )
