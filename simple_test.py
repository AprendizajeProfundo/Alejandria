import sys
import os

# Asegurarse de que estamos en el directorio correcto
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Directorio actual: {os.getcwd()}")

# Añadir el directorio del backend al path
sys.path.insert(0, os.path.abspath('alejandria/backend'))
print(f"\nBuscando en las siguientes rutas:")
for p in sys.path:
    print(f"- {p}")

# Intentar importar el módulo
try:
    from src.scraping.agent_arxiv import ArxivAgent
    print("\n¡Módulo importado exitosamente!")
    
    # Probar el agente
    print("\nProbando búsqueda en ArXiv...")
    agent = ArxivAgent()
    results = agent.search_papers("RAPTOR", max_results=3)
    
    # Mostrar resultados
    print(f"\nSe encontraron {len(results)} resultados:")
    for i, paper in enumerate(results, 1):
        print(f"\n--- Paper {i} ---")
        print(f"Título: {paper['title']}")
        print(f"Autores: {paper['authors']}")
        print(f"Enlace: {paper['link']}")
        print(f"Resumen: {paper['summary'][:150]}...")
        
except ImportError as e:
    print(f"\nError al importar: {e}")
    import traceback
    traceback.print_exc()
    
    # Mostrar el contenido del directorio
    print("\nContenido de alejandria/backend/src/scraping/:")
    try:
        for f in os.listdir('alejandria/backend/src/scraping'):
            print(f"- {f}")
    except Exception as e:
        print(f"No se pudo listar el directorio: {e}")
