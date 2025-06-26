import os
import logging
from dotenv import load_dotenv

# Importa AssistantAgent de autogen_agentchat.agents (fallback comprobado)
from autogen_agentchat.agents import AssistantAgent
from alejandria.domain.base_agent import BaseAgent
from alejandria.domain.agent_response import AgentResponse

# Carga variables de entorno
load_dotenv()


class EmpathyAgent(BaseAgent):
    name = "EmpathyAgent"
    instructions = "Responde con empatía y comprensión usando LLM AutoGen."

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
        logging.info(f"[EmpathyAgent] Inicializando con modelo: {self.llm_model}")
        self.agent = AssistantAgent(
            name="EmpathyAgent",
            model_client=None,
            system_message=(self.system_message),
        )

    async def act(self, req):
        try:
            # Llamada normal (no streaming)
            response = await self.agent.run(task=req.message)
            content = str(response)
        except Exception as e:
            logging.error(f"[EmpathyAgent] ERROR: {e}")
            content = f"[AutoGen] Error: {e}"
        return AgentResponse(agent_name=self.name, content=content, meta={})

    async def act_stream(self, req, on_token):
        # on_token: callback(str) -> None
        try:
            buffer = ""

            def cb(token):
                nonlocal buffer
                buffer += token
                on_token(token)

            await self.agent.run(task=req.message, stream=True, on_token=cb)
            return AgentResponse(
                agent_name=self.name,
                content=buffer,
                meta={},
            )
        except Exception as e:
            logging.error(f"[EmpathyAgent] ERROR: {e}")
            on_token(f"[AutoGen] Error: {e}")
            return AgentResponse(
                agent_name=self.name, content=f"[AutoGen] Error: {e}", meta={}
            )
