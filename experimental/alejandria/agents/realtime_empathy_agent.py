import os
import logging
from dotenv import load_dotenv
from autogen.agentchat.realtime.experimental.realtime_agent import RealtimeAgent
from domain.base_agent import BaseAgent
from domain.agent_response import AgentResponse

# Carga variables de entorno
load_dotenv()


class RealtimeEmpathyAgent(BaseAgent):
    name = "RealtimeEmpathyAgent"
    instructions = "Responde con empatía y comprensión usando RealtimeAgent de AutoGen."

    def __init__(self, api_key=None, model=None, system_message=None):
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.system_message = system_message or os.getenv(
            "EMPATHY_SYSTEM_MESSAGE",
            (
                "Eres un asistente empático que responde con "
                "comprensión y apoyo emocional."
            ),
        )
        logging.info(
            "[RealtimeEmpathyAgent] Inicializando con modelo: " f"{self.llm_model}"
        )
        self.agent = RealtimeAgent(
            name="RealtimeEmpathyAgent",
            system_message=self.system_message,
            llm_config={"model": self.llm_model, "api_key": self.openai_api_key},
        )

    async def act(self, req):
        try:
            await self.agent.start_observers()
            await self.agent.realtime_client.session_update(
                session_options={"instructions": (self.system_message)}
            )
            await self.agent.realtime_client.send_message(req.message)
            buffer = ""
            async for event in self.agent.realtime_client.read_events():
                if hasattr(event, "content"):
                    buffer += event.content
            return AgentResponse(agent_name=self.name, content=buffer, meta={})
        except Exception as e:
            logging.error(f"[RealtimeEmpathyAgent] ERROR: {e}")
            return AgentResponse(
                agent_name=self.name,
                content=f"[RealtimeAgent] Error: {e}",
                meta={},
            )

    async def act_stream(self, req, on_token):
        # Ejecuta el agente en modo realtime, enviando tokens al callback
        try:
            await self.agent.start_observers()
            await self.agent.realtime_client.session_update(
                session_options={"instructions": (self.system_message)}
            )
            await self.agent.realtime_client.send_message(req.message)
            buffer = ""
            async for event in self.agent.realtime_client.read_events():
                if hasattr(event, "content"):
                    token = event.content
                    buffer += token
                    on_token(token)
            return AgentResponse(agent_name=self.name, content=buffer, meta={})
        except Exception as e:
            logging.error(f"[RealtimeEmpathyAgent] ERROR: {e}")
            on_token(f"[RealtimeAgent] Error: {e}")
            return AgentResponse(
                agent_name=self.name,
                content=f"[RealtimeAgent] Error: {e}",
                meta={},
            )
