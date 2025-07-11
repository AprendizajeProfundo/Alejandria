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

    async def handle_stream(self, req: UserMessage, on_token, history=None):
        agents = [
            self.registry.get("autogen_empathy"),
            self.registry.get("autogen_social"),
            self.registry.get("autogen_gamification"),
        ]
        agent_contents = [None] * len(agents)

        # El historial es una lista de dicts: {from, text, agent?}
        if history is None:
            history = []
        def build_agent_context():
            context = []
            for h in history:
                if h.get('from') == 'user':
                    context.append(f"Usuario: {h['text']}")
                elif h.get('from') == 'agent' and h.get('agent'):
                    context.append(f"{h['agent']}: {h['text']}")
            return '\n'.join(context)

        async def run_agent(idx, agent):
            buffer = ""
            # El contexto de cada agente incluye TODO el historial
            full_message = build_agent_context() + ("\n" if history else "") + req.message
            print(f"[Orchestrator] Contexto para {agent.name}:\n{full_message}\n{'-'*40}")
            agent_req = UserMessage(user_id=req.user_id, message=full_message)
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
            result = await agent.act_stream(agent_req, agent_on_token)
            agent_contents[idx] = result.content

        # Lanzar todos los agentes en paralelo
        await asyncio.gather(*(run_agent(i, agent) for i, agent in enumerate(agents)))
        # Formatear la entrada al manager con bloques claros y markdown
        def format_agent_block(agent, content):
            return f"**--- {agent.name} ---**\n\n" + content.strip()
        combined = "\n\n".join(
            format_agent_block(agent, content) for agent, content in zip(agents, agent_contents) if content
        )
        manager = self.registry.get("manager")
        # El contexto del manager también incluye TODO el historial
        manager_context = build_agent_context()
        manager_full_message = manager_context + ("\n" if manager_context else "") + combined
        print(f"[Orchestrator] Contexto para manager:\n{manager_full_message}\n{'='*40}")
        manager_req = UserMessage(user_id=req.user_id, message=manager_full_message)

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
