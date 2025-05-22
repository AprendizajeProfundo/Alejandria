"""
Servicio de búsqueda que coordina los diferentes agentes de búsqueda.
"""
from typing import Dict, List, Any
import logging
from ..scraping.source_processor import SourceProcessor

logger = logging.getLogger(__name__)

class SearchService:
    """
    Servicio para manejar búsquedas a través de múltiples fuentes.
    """
    
    def __init__(self):
        """Inicializa el servicio de búsqueda."""
        self.source_processor = SourceProcessor()
        logger.info("SearchService inicializado")
    
    async def search(
        self,
        query: str,
        sources: List[str] = None,
        websocket = None,
        max_results: int = 10,
        sortby: str = "relevance",
        type_query: str = "all",
        start: int = 0,
        sortorder: str = "descending"
    ) -> Dict[str, Any]:
        """
        Realiza una búsqueda en Arxiv.
        
        Args:
            query: Término de búsqueda
            sources: No utilizado, se mantiene por compatibilidad
            websocket: Objeto WebSocket opcional para actualizaciones en tiempo real
            max_results: Número máximo de resultados a retornar
            sortby: Criterio de ordenamiento de los resultados
            type_query: Tipo de consulta a realizar
            start: Índice de inicio para los resultados
            sortorder: Orden de clasificación (ascendente/descendente)
            
        Returns:
            Dict con los resultados de la búsqueda en Arxiv
        """
        from datetime import datetime  # Mover al inicio del archivo
        
        # Forzar solo búsqueda en Arxiv
        sources = ['arxiv']
        logger.info(f"Iniciando búsqueda para: '{query}' en Arxiv")
        logger.info(f"[search_service] Recibido: query={query}, max_results={max_results}, sortby={sortby}, type_query={type_query}, start={start}, sortorder={sortorder}")
        
        try:
            # Procesar solo Arxiv con soporte para websocket
            results = await self.source_processor.process_sources(
                query=query,
                sources=sources,
                websocket=websocket,
                max_results=max_results,
                sortby=sortby,
                type_query=type_query,
                start=start,
                sortorder=sortorder
            )
            
            logger.info(f"Búsqueda completada exitosamente con {sum(len(r) for r in results.values())} resultados")
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "sources": sources
            }
            
        except Exception as e:
            error_msg = f"Error en la búsqueda: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Notificar error a través del websocket si está disponible
            if websocket:
                try:
                    await websocket.send_json({
                        "type": "error",
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as ws_error:
                    logger.error(f"Error enviando error al websocket: {str(ws_error)}")
            
            return {
                "status": "error",
                "error": error_msg,
                "query": query,
                "results": {}
            }
