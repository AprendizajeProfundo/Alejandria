from alejandria.agents.empathy_agent import EmpathyAgent
from alejandria.agents.autogen_empathy_agent import AutoGenEmpathyAgent
from alejandria.agents.autogen_social_agent import AutoGenSocialAgent
from alejandria.agents.autogen_gamification_agent import (
    AutoGenGamificationAgent,
)
from alejandria.agents.prompts import (
    AUTOGEN_EMPATHY_PROMPT,
    AUTOGEN_SOCIAL_PROMPT,
    AUTOGEN_GAMIFICATION_PROMPT,
    MANAGER_PROMPT,
)


class AgentRegistry:
    def __init__(self):
        self.agents = {
            "empathy": EmpathyAgent(
                system_message=(
                    "Eres un/a docente-IA empático/a.\n"
                    "1. Identifica la emoción principal del usuario y "
                    "nómbrala explícitamente.\n"
                    "2. Relaciona esa emoción con una situación educativa "
                    "concreta.\n"
                    "3. Ofrece una microacción de autocuidado o validación "
                    "emocional.\n"
                    "4. Termina con una pregunta breve para seguir la "
                    "conversación.\n"
                    "Sé breve, cálido/a y concreto/a. No respondas "
                    "directamente al usuario, solo entrega tu análisis "
                    "para la síntesis final."
                )
            ),
            "autogen_empathy": AutoGenEmpathyAgent(
                system_message=AUTOGEN_EMPATHY_PROMPT
            ),
            "autogen_social": AutoGenSocialAgent(system_message=AUTOGEN_SOCIAL_PROMPT),
            "autogen_gamification": AutoGenGamificationAgent(
                system_message=(AUTOGEN_GAMIFICATION_PROMPT)
            ),
            "manager": AutoGenEmpathyAgent(system_message=(MANAGER_PROMPT)),
        }

    def get(self, agent_key):
        return self.agents.get(agent_key)

    def all(self):
        return list(self.agents.values())
