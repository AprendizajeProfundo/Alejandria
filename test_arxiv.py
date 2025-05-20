import asyncio
import sys
import os

# Añadir el directorio del backend al path de Python
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'alejandria/backend'))
sys.path.insert(0, backend_path)

# Ahora podemos importar el agente
try:
    from src.scraping.agent_arxiv import ArxivAgent
except ImportError as e:
    print(f"Error al importar: {e}")
    print(f"sys.path: {sys.path}")
    raise

async def test_arxiv():
    print("=== Probando agente de ArXiv ===")
    agent = ArxivAgent()
    
    # Probar búsqueda
    print("\nBuscando papers sobre 'RAPTOR'...")
    results = agent.search_papers("RAPTOR", max_results=3)
    
    # Mostrar resultados
    print(f"\nSe encontraron {len(results)} resultados:")
    for i, paper in enumerate(results, 1):
        print(f"\n--- Paper {i} ---")
        print(f"Título: {paper['title']}")
        print(f"Autores: {paper['authors']}")
        print(f"Enlace: {paper['link']}")
        print(f"Resumen: {paper['summary'][:150]}...")

if __name__ == "__main__":
    asyncio.run(test_arxiv())
