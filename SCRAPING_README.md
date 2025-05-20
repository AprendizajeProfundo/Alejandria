# Módulo de Scraping para Alejandria

Este módulo se encarga de la extracción de artículos de diferentes fuentes como ArXiv, Towards Data Science y Medium.

## Fuentes soportadas

1. **ArXiv**
   - Búsqueda de artículos académicos
   - Sin necesidad de API key

2. **Towards Data Science (TDS)**
   - Web scraping de artículos técnicos
   - No requiere API key

3. **Medium** (Opcional)
   - Requiere API key de RapidAPI
   - Permite búsquedas avanzadas

## Configuración

1. Instalar dependencias:
   ```bash
   pip install -r requirements-scraping.txt
   ```

2. Copiar el archivo de ejemplo de variables de entorno:
   ```bash
   cp .env.example .env
   ```

3. Configurar las variables de entorno en `.env`:
   ```
   # API Key para Medium (opcional)
   MEDIUM_API_KEY=tu_api_key_aquí
   ```

## Uso básico

```python
from scraping.source_processor import SourceProcessor
import asyncio

async def main():
    processor = SourceProcessor()
    
    # Buscar artículos en todas las fuentes
    results = await processor.process_sources(
        query="machine learning",
        sources=["arxiv", "tds", "medium"],
        timeout=30
    )
    
    # Imprimir resultados
    for source, articles in results.items():
        print(f"\n=== {source.upper()} === ({len(articles)} resultados)")
        for article in articles:
            print(f"\n{article['title']}")
            print(f"Autor(es): {article.get('authors', 'Desconocido')}")
            print(f"URL: {article.get('url')}")
            print(f"Publicado: {article.get('published')}")
            print(f"Resumen: {article.get('summary', '')[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

## Estructura del proyecto

```
src/scraping/
├── __init__.py
├── agent_arxiv.py     # Agente para ArXiv
├── agent_tds.py      # Agente para Towards Data Science
├── agent_medium.py   # Agente para Medium (opcional)
├── source_processor.py  # Procesador principal
└── utils.py          # Utilidades comunes
```

## Contribuir

1. Instalar dependencias de desarrollo:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Ejecutar pruebas:
   ```bash
   pytest tests/
   ```

3. Formatear código:
   ```bash
   black .
   isort .
   ```

## Notas

- El módulo está diseñado para ser asíncrono y eficiente.
- Se recomienda implementar un sistema de caché para evitar solicitudes repetidas.
- Respetar los términos de servicio de cada fuente.
