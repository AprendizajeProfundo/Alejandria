from alejandria.services.agent_registry import AgentRegistry
from alejandria.domain.agent_response import AgentResponse
from alejandria.domain.user_message import UserMessage
import asyncio
import inspect


class OrchestratorService:
    def __init__(self, registry=None):
        self.registry = registry or AgentRegistry()

    async def handle(self, req: UserMessage):
        agents = [
            self.registry.get("autogen_empathy"),
            self.registry.get("autogen_social"),
            self.registry.get("autogen_gamification"),
        ]
        # Ejecutar agentes en paralelo
        results = await asyncio.gather(*(agent.act(req) for agent in agents))
        combined = "\n\n".join([r.content for r in results])
        meta = {r.agent_name: r.meta for r in results}
        manager = self.registry.get("manager")
        manager_req = UserMessage(user_id=req.user_id, message=combined)
        manager_result = await manager.act(manager_req)
        return AgentResponse(
            agent_name="Manager/Educador",
            content=manager_result.content,
            meta=meta,
        )

    async def handle_stream(self, req: UserMessage, on_token):
        agents = [
            self.registry.get("autogen_empathy"),
            self.registry.get("autogen_social"),
            self.registry.get("autogen_gamification"),
        ]
        agent_contents = [None] * len(agents)

        async def run_agent(idx, agent):
            buffer = ""

            async def agent_on_token(token, agent_name=agent.name):
                nonlocal buffer
                buffer += token
                if on_token and inspect.iscoroutinefunction(on_token):
                    await on_token(
                        {
                            "agent_name": agent_name,
                            "content": token,
                            "is_manager": False,
                        }
                    )
                elif on_token:
                    on_token(
                        {
                            "agent_name": agent_name,
                            "content": token,
                            "is_manager": False,
                        }
                    )

            result = await agent.act_stream(req, agent_on_token)
            agent_contents[idx] = result.content

        # Lanzar todos los agentes en paralelo
        await asyncio.gather(*(run_agent(i, agent) for i, agent in enumerate(agents)))
        # Formatear la entrada al manager con bloques claros
        combined = "\n\n".join(
            f"--- {agent.name} ---\n{content.strip()}" for agent, content in zip(agents, agent_contents) if content
        )
        manager = self.registry.get("manager")
        manager_req = UserMessage(user_id=req.user_id, message=combined)

        async def manager_on_token(token):
            if on_token and inspect.iscoroutinefunction(on_token):
                await on_token(
                    {"agent_name": "manager", "content": token, "is_manager": True}
                )
            elif on_token:
                on_token(
                    {"agent_name": "manager", "content": token, "is_manager": True}
                )

        await manager.act_stream(manager_req, manager_on_token)
