# agent_congruence.py

import json

def check_congruence(summaries):
    """
    Dado un dict de la forma:
    {
      "paper1_id": {"main_ideas": [...], "methods": [...], ...},
      "paper2_id": {"main_ideas": [...], "methods": [...], ...},
      ...
    }
    Retorna una estructura que indique qué tan afines son los papers,
    y/o un 'consensus_summary' unificado para papers muy similares.
    """
    # Ejemplo simplificado: si comparten >= 1 main_idea => hay afinidad
    # (en la práctica, se podría usar un LLM adicional o un vector embedding.)
    papers = list(summaries.keys())
    results = {}
    for i, pid1 in enumerate(papers):
        for pid2 in papers[i+1:]:
            intersection = set(summaries[pid1]["main_ideas"]) & set(summaries[pid2]["main_ideas"])
            is_congruent = len(intersection) > 0
            results[(pid1, pid2)] = {
                "congruence": is_congruent,
                "shared_main_ideas": list(intersection)
            }
    return results
