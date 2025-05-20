#!/usr/bin/env python3
"""
Script de prueba para el módulo de scraping.

Ejemplo de uso:
    python test_scraping.py "machine learning" --sources arxiv tds medium
"""
import asyncio
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

# Asegurarse de que el directorio src está en el path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.absolute()))

from src.scraping.source_processor import SourceProcessor

async def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Buscar artículos en diferentes fuentes')
    parser.add_argument('query', type=str, help='Término de búsqueda')
    parser.add_argument('--sources', nargs='+', 
                       default=['arxiv', 'tds', 'medium'],
                       choices=['arxiv', 'tds', 'medium'],
                       help='Fuentes a consultar')
    parser.add_argument('--max-results', type=int, default=5,
                       help='Número máximo de resultados por fuente')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Tiempo máximo de espera por fuente (segundos)')
    parser.add_argument('--output', type=str,
                       help='Archivo de salida para guardar los resultados (JSON)')
    
    args = parser.parse_args()
    
    print(f"""
    ===================================================
    INICIANDO BÚSQUEDA
    Consulta: {args.query}
    Fuentes: {', '.join(args.sources)}
    Máx. resultados: {args.max_results}
    Timeout: {args.timeout}s
    ===================================================
    """)
    
    # Inicializar el procesador de fuentes
    processor = SourceProcessor()
    
    # Obtener información de las fuentes disponibles
    source_info = processor.get_source_info()
    print("\nFuentes disponibles:")
    for source in source_info['sources']:
        print(f"- {source['name']} ({source['id']}): {source['description']}")
    
    # Verificar fuentes solicitadas
    available_sources = [s['id'] for s in source_info['sources']]
    invalid_sources = [s for s in args.sources if s not in available_sources]
    
    if invalid_sources:
        print(f"\n⚠️  Advertencia: Las siguientes fuentes no están disponibles: {', '.join(invalid_sources)}")
        args.sources = [s for s in args.sources if s in available_sources]
    
    if not args.sources:
        print("\n❌ No hay fuentes válidas para buscar")
        return
    
    # Realizar la búsqueda
    print(f"\n🔍 Buscando en: {', '.join(args.sources)}")
    start_time = datetime.now()
    
    try:
        results = await processor.process_sources(
            query=args.query,
            sources=args.sources,
            timeout=args.timeout
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Mostrar resumen
        print(f"\n✅ Búsqueda completada en {elapsed:.2f} segundos")
        print("=" * 50)
        
        total_results = 0
        for source, articles in results.items():
            print(f"\n📚 {source.upper()} - {len(articles)} resultados")
            total_results += len(articles)
            
            for i, article in enumerate(articles[:args.max_results], 1):
                print(f"\n  {i}. {article['title']}")
                print(f"     Autor(es): {article.get('authors', 'Desconocido')}")
                print(f"     Publicado: {article.get('published', '')}")
                print(f"     URL: {article.get('url', '')}")
                
                # Mostrar resumen si está disponible
                if 'summary' in article and article['summary']:
                    summary = article['summary']
                    print(f"     Resumen: {summary[:150]}..." if len(summary) > 150 else f"     Resumen: {summary}")
                
                # Mostrar información adicional específica de la fuente
                if source == 'arxiv':
                    print(f"     Categorías: {article.get('categories', '')}")
                elif source == 'medium':
                    print(f"     Tiempo lectura: {article.get('read_time', '?')} min")
                    print(f"     Aplausos: {article.get('claps', 0)}")
        
        print(f"\n📊 Total de resultados: {total_results}")
        
        # Guardar resultados si se especificó un archivo de salida
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Resultados guardados en: {args.output}")
    
    except Exception as e:
        print(f"\n❌ Error durante la búsqueda: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
