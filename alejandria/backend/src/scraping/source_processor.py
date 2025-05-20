from typing import Dict, List, Any, Optional, Union
import time
import asyncio
from datetime import datetime
import logging

# Importar agentes
from .agent_arxiv import ArxivAgent
from .agent_tds import TdsAgent

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SourceProcessor:
    def __init__(self):
        """Inicializa el procesador de fuentes solo con Arxiv."""
        logger.info("="*80)
        logger.info("INICIALIZANDO PROCESADOR DE FUENTES (SOLO ARXIV)")
        logger.info("="*80)
        
        # Inicializar solo el agente de Arxiv
        logger.info("\nInicializando agente de Arxiv...")
        self.arxiv_agent = ArxivAgent()
        
        # Configurar solo Arxiv como fuente disponible
        self.sources = {'arxiv': self._process_arxiv}
        
        logger.info("\nFuente configurada: ['arxiv']")
        logger.info("="*80 + "\n")

    def _format_date(self, date_str: str) -> Optional[str]:
        """Formatea una fecha a un formato legible."""
        if not date_str:
            return None
            
        try:
            # Para fechas de arXiv
            if 'T' in date_str and 'Z' in date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                return dt.strftime('%Y-%m-%d')
            # Para fechas de TDS
            elif 'T' in date_str and '+' in date_str:
                dt = datetime.strptime(date_str.split('+')[0], '%Y-%m-%dT%H:%M:%S')
                return dt.strftime('%Y-%m-%d')
            return date_str
        except Exception as e:
            print(f"[SourceProcessor] Error formateando fecha {date_str}: {e}")
            return date_str
            
    def _format_authors(self, authors: List[Dict[str, str]]) -> str:
        """Formatea la lista de autores a un string."""
        if not authors:
            return ""
        return ", ".join([a.get("name", "") for a in authors if a.get("name")])

    async def process_sources(
        self, 
        query: str, 
        sources: List[str],
        websocket = None,
        timeout: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Procesa la consulta en Arxiv y envía los resultados a través del websocket.
        
        Args:
            query: Término de búsqueda
            sources: No utilizado, se mantiene por compatibilidad
            websocket: Objeto WebSocket para enviar actualizaciones
            timeout: Tiempo máximo para la búsqueda en segundos
            
        Returns:
            Diccionario con los resultados de Arxiv
        """
        start_time = time.time()
        results = {}
        source = 'arxiv'  # Siempre usamos Arxiv
        
        logger.info(f"Iniciando búsqueda en Arxiv")
        
        # Función para enviar actualizaciones al websocket
        async def send_update(status: str, data: Any = None, error: str = None, results: List[Dict] = None):
            if not websocket:
                return
                
            message = {
                "type": "update",
                "source": source,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if data is not None:
                message["data"] = data
            if error is not None:
                message["error"] = error
            if results is not None:
                message["results"] = results
                
            try:
                await websocket.send_json(message)
                # Asegurarse de que el mensaje se envíe inmediatamente
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error enviando actualización al websocket: {str(e)}", exc_info=True)
        
        # Procesar solo Arxiv
        source_start = time.time()
        source_results = []
        
        try:
            # Notificar inicio de procesamiento de la fuente
            await send_update("started")
            logger.info("Procesando Arxiv...")
            
            # Procesar la fuente con timeout
            source_task = asyncio.create_task(
                self._process_source('arxiv', query),
                name="arxiv_task"
            )
            
            try:
                # Esperar con timeout
                source_results = await asyncio.wait_for(
                    source_task,
                    timeout=timeout
                )
                
                # Notificar resultados exitosos
                results['arxiv'] = source_results
                
                # Enviar resultados a medida que se obtienen
                if source_results:
                    await send_update(
                        status="results",
                        data={"count": len(source_results)},
                        results=source_results  # Enviar todos los resultados
                    )
                
                # Notificar finalización
                await send_update(
                    status="completed",
                    data={"count": len(source_results)}
                )
                
                logger.info(f"Arxiv completado: {len(source_results)} resultados")
                
            except asyncio.TimeoutError:
                if not source_task.done():
                    source_task.cancel()
                error_msg = "Tiempo de espera agotado para Arxiv"
                logger.warning(error_msg)
                await send_update("timeout", error=error_msg)
                results['arxiv'] = []
                
        except Exception as e:
            error_msg = f"Error procesando Arxiv: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await send_update("error", error=error_msg)
            results['arxiv'] = []
            
        finally:
            # Asegurarse de que la tarea se cancele si aún está en ejecución
            if 'source_task' in locals() and not source_task.done():
                source_task.cancel()
            
            elapsed = time.time() - source_start
            logger.info(f"Tiempo en Arxiv: {elapsed:.2f}s")
        
        # Enviar resumen final
        total_results = sum(len(r) for r in results.values())
        elapsed_total = time.time() - start_time
        
        if websocket:
            try:
                await websocket.send_json({
                    "type": "summary",
                    "sources_searched": 1,  # Solo Arxiv
                    "total_results": total_results,
                    "time_elapsed": f"{elapsed_total:.2f}s"
                })
            except Exception as e:
                logger.error(f"Error enviando resumen: {str(e)}")
        
        logger.info(
            f"Procesamiento completado en {elapsed_total:.2f}s. "
            f"Total de resultados: {total_results}"
        )
        
        return results

    async def _process_source(self, source: str, query: str) -> List[Dict[str, Any]]:
        """Procesa la consulta en una fuente específica."""
        if source not in self.sources:
            logger.warning(f"No se puede procesar la fuente {source}: no está disponible")
            return []
        
        try:
            return await self.sources[source](query)
        except Exception as e:
            logger.error(f"Error procesando fuente {source}: {str(e)}")
            return []

    async def _process_arxiv(self, query: str) -> List[Dict[str, Any]]:
        """
        Procesa la consulta usando ArXiv.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de artículos de ArXiv
        """
        try:
            logger.info(f"Buscando en ArXiv: {query}")
            
            # Obtener resultados de ArXiv con manejo de errores
            try:
                # Usar search_papers en lugar de search_articles
                arxiv_results = self.arxiv_agent.search_papers(query=query, max_results=10)
                if not isinstance(arxiv_results, list):
                    logger.warning("La respuesta de ArXiv no es una lista")
                    return []
            except Exception as e:
                logger.error(f"Error al obtener resultados de ArXiv: {str(e)}", exc_info=True)
                return []
            
            processed_results = []
            for result in arxiv_results:
                try:
                    if not isinstance(result, dict):
                        logger.warning(f"Resultado de ArXiv no es un diccionario: {result}")
                        continue
                        
                    # Extraer información básica con valores por defecto seguros
                    title = result.get("title", "Sin título").strip()
                    abstract = result.get("summary", result.get("abstract", "")).strip()
                    
                    # Procesar autores
                    authors = []
                    if "authors" in result:
                        authors_str = result["authors"]
                        if isinstance(authors_str, str):
                            # Formato: "Author1, Author2, ..."
                            authors = [{"name": author.strip()} for author in authors_str.split(",") if author.strip()]
                        elif isinstance(authors_str, list):
                            authors = [{"name": str(author).strip()} for author in authors_str if str(author).strip()]
                    
                    # Procesar categorías (usar main_topics si está disponible)
                    categories = []
                    if "main_topics" in result and isinstance(result["main_topics"], list):
                        categories = [str(topic).strip() for topic in result["main_topics"] if str(topic).strip()]
                    
                    # Obtener URL y extraer ID de arXiv
                    arxiv_url = result.get("link", "")
                    entry_id = ""
                    if arxiv_url:
                        # Intentar extraer el ID de la URL (formato: https://arxiv.org/abs/1234.56789)
                        import re
                        match = re.search(r'arxiv\.org\/abs\/([^\/]+)', arxiv_url)
                        if match:
                            entry_id = f"arxiv:{match.group(1)}"
                    
                    # Construir el resultado procesado
                    processed = {
                        "id": f"arxiv-{entry_id}" if entry_id else f"arxiv-{hash(title)}",
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "published": self._format_date(result.get("published", "")),
                        "categories": categories,
                        "primary_category": categories[0] if categories else "",
                        "pdf_url": arxiv_url.replace("/abs/", "/pdf/") + ".pdf" if arxiv_url else "",
                        "url": arxiv_url,
                        "source": "ArXiv",
                        "relevance": self._calculate_relevance({
                            "title": title,
                            "abstract": abstract
                        }, query)
                    }
                    
                    # Añadir campos opcionales
                    optional_fields = [
                        "github_link", "github_status", "comment",
                        "doi", "journal_ref", "comment"
                    ]
                    for field in optional_fields:
                        if field in result and result[field] is not None:
                            processed[field] = result[field]
                    
                    processed_results.append(processed)
                    
                except Exception as e:
                    logger.error(f"Error procesando resultado de ArXiv: {str(e)}", exc_info=True)
                    continue
            
            logger.info(f"ArXiv devolvió {len(processed_results)} resultados válidos de {len(arxiv_results)} obtenidos")
            return processed_results
            
        except Exception as e:
            error_msg = f"Error en la búsqueda de ArXiv: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []

    async def _process_tds(self, query: str) -> List[Dict[str, Any]]:
        """
        Procesa la consulta usando Towards Data Science.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de artículos de Towards Data Science
        """
        if not hasattr(self, 'tds_agent') or not self.tds_agent:
            logger.warning("El agente de TDS no está disponible")
            return []
            
        try:
            logger.info(f"Buscando en Towards Data Science: {query}")
            
            # Obtener resultados de TDS
            tds_results = self.tds_agent.search_articles(query=query)
            if not isinstance(tds_results, list):
                logger.warning("La respuesta de TDS no es una lista")
                return []
            
            processed_results = []
            for result in tds_results:
                try:
                    # Asegurar que el resultado sea un diccionario
                    if not isinstance(result, dict):
                        logger.warning(f"Resultado de TDS no es un diccionario: {result}")
                        continue
                        
                    # Extraer información básica
                    title = result.get("title", "Sin título")
                    abstract = result.get("summary", "")
                    
                    # Procesar autores
                    authors = []
                    if "authors" in result:
                        if isinstance(result["authors"], list):
                            authors = [{"name": str(author)} for author in result["authors"]]
                        elif isinstance(result["authors"], str):
                            authors = [{"name": result["authors"]}]
                    
                    # Procesar categorías
                    categories = []
                    if "categories" in result:
                        if isinstance(result["categories"], list):
                            categories = [str(cat) for cat in result["categories"]]
                        elif isinstance(result["categories"], str):
                            categories = result["categories"].split()
                    
                    # Construir el resultado procesado
                    processed = {
                        "id": f"tds-{result.get('id', '')}",
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "published": result.get("published", ""),
                        "categories": categories,
                        "primary_category": result.get("primary_category", categories[0] if categories else ""),
                        "pdf_url": result.get("pdf_url", ""),
                        "url": result.get("url", ""),
                        "source": "Towards Data Science",
                        "relevance": self._calculate_relevance({
                            "title": title,
                            "abstract": abstract
                        }, query)
                    }
                    
                    # Añadir campos opcionales
                    optional_fields = ["github_link", "github_status", "comment"]
                    for field in optional_fields:
                        if field in result:
                            processed[field] = result[field]
                    
                    processed_results.append(processed)
                    
                except Exception as e:
                    logger.error(f"Error procesando resultado de TDS: {str(e)}")
                    continue
            
            logger.info(f"TDS devolvió {len(processed_results)} resultados")
            return processed_results
            
        except Exception as e:
            error_msg = f"Error en la búsqueda de TDS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []

    def _calculate_relevance(self, article: Dict[str, Any], query: str) -> float:
        """
        Calcula la relevancia de un artículo basado en la consulta.
        
        Args:
            article: Diccionario con la información del artículo
            query: Término de búsqueda
            
        Returns:
            Puntuación de relevancia entre 0 y 1
        """
        try:
            # Convertir todo a minúsculas para hacer la búsqueda insensible a mayúsculas
            query_terms = query.lower().split()
            title = article.get('title', '').lower()
            abstract = article.get('abstract', '').lower()
            
            # Contar ocurrencias de términos de búsqueda
            title_matches = sum(term in title for term in query_terms)
            abstract_matches = sum(term in abstract for term in query_terms)
            
            # Ponderar más los términos en el título
            score = (title_matches * 0.7) + (abstract_matches * 0.3)
            
            # Normalizar el puntaje entre 0 y 1
            max_possible = len(query_terms) * 0.7  # Máximo puntaje posible
            normalized_score = min(score / max_possible if max_possible > 0 else 0, 1.0)
            
            return round(normalized_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculando relevancia: {str(e)}")
            return 0.0
            
    async def _process_tds(self, query: str) -> List[Dict[str, Any]]:
        """
        Procesa la consulta usando Towards Data Science.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de artículos encontrados, puede estar vacía si hay errores
        """
        if not hasattr(self, 'tds_agent') or not self.tds_agent:
            logger.warning("El agente de TDS no está disponible")
            return []
            
        try:
            logger.info(f"Buscando en Towards Data Science: {query}")
            
            # Obtener resultados de TDS con manejo de errores
            try:
                # Verificar si el agente TDS tiene el método search_articles
                if not hasattr(self.tds_agent, 'search_articles'):
                    logger.error("El agente TDS no tiene el método 'search_articles'")
                    return []
                    
                results = self.tds_agent.search_articles(query=query, max_results=10)
                if not isinstance(results, list):
                    logger.warning("La respuesta de TDS no es una lista")
                    return []
            except Exception as e:
                logger.error(f"Error al obtener resultados de TDS: {str(e)}", exc_info=True)
                return []
            
            processed_results = []
            for result in results:
                try:
                    if not isinstance(result, dict):
                        logger.warning(f"Resultado de TDS no es un diccionario: {result}")
                        continue
                        
                    # Extraer información básica con valores por defecto seguros
                    title = result.get("title", "Sin título").strip()
                    summary = result.get("summary", result.get("abstract", "")).strip()
                    
                    # Procesar autores
                    authors = []
                    if "authors" in result:
                        authors_data = result["authors"]
                        if isinstance(authors_data, list):
                            authors = [{"name": str(author).strip()} for author in authors_data if str(author).strip()]
                        elif isinstance(authors_data, str):
                            authors = [{"name": author.strip()} for author in authors_data.split(",") if author.strip()]
                    elif "author" in result and result["author"]:
                        author_str = result["author"]
                        if isinstance(author_str, str):
                            authors = [{"name": author_str.strip()}]
                    
                    # Procesar categorías/etiquetas
                    categories = []
                    for field in ["categories", "tags", "topics"]:
                        if field in result and result[field]:
                            if isinstance(result[field], list):
                                categories.extend([str(tag).strip() for tag in result[field] if str(tag).strip()])
                            elif isinstance(result[field], str):
                                categories.extend([tag.strip() for tag in result[field].split(",") if tag.strip()])
                    
                    # Eliminar duplicados
                    categories = list(dict.fromkeys(categories))
                    
                    # Obtener URL y generar ID único si es necesario
                    url = result.get("url", result.get("link", "")).strip()
                    entry_id = result.get("id", "")
                    if not entry_id and url:
                        # Intentar extraer un ID de la URL
                        import re
                        match = re.search(r'/([a-f0-9]{32,})/?$', url)
                        if match:
                            entry_id = match.group(1)
                    
                    # Construir el resultado procesado
                    processed_result = {
                        "id": f"tds-{entry_id}" if entry_id else f"tds-{hash(title)}",
                        "title": title,
                        "abstract": summary,
                        "authors": authors,
                        "published": self._format_date(result.get("published", result.get("date", ""))),
                        "categories": categories,
                        "primary_category": categories[0] if categories else "",
                        "url": url,
                        "source": "Towards Data Science",
                        "relevance": self._calculate_relevance({
                            "title": title,
                            "abstract": summary
                        }, query)
                    }
                    
                    # Añadir campos opcionales
                    optional_fields = [
                        "pdf_url", "github_link", "github_status",
                        "read_time", "reading_time", "claps", "comment",
                        "publication", "subtitle", "language"
                    ]
                    for field in optional_fields:
                        if field in result and result[field] is not None:
                            # Convertir campos de tiempo de lectura a segundos si es necesario
                            if field in ["read_time", "reading_time"] and isinstance(result[field], str):
                                try:
                                    # Asumir formato como "5 min read"
                                    if "min" in result[field]:
                                        processed_result[field] = int(result[field].split()[0]) * 60
                                    elif "hour" in result[field]:
                                        processed_result[field] = int(result[field].split()[0]) * 3600
                                    else:
                                        processed_result[field] = int(result[field])
                                except (ValueError, IndexError):
                                    processed_result[field] = 0
                            else:
                                processed_result[field] = result[field]
                    
                    processed_results.append(processed_result)
                    
                except Exception as e:
                    logger.error(f"Error procesando resultado de TDS: {str(e)}", exc_info=True)
                    continue
            
            logger.info(f"TDS devolvió {len(processed_results)} resultados válidos de {len(results)} obtenidos")
            return processed_results
            
        except Exception as e:
            error_msg = f"Error en la búsqueda de TDS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []

    def get_source_info(self) -> Dict[str, Any]:
        """
        Devuelve información sobre las fuentes disponibles
        
        Returns:
            Dict con información de las fuentes disponibles
        """
        sources = [
            {
                'id': 'arxiv', 
                'name': 'ArXiv', 
                'description': 'Artículos académicos',
                'available': True
            },
            {
                'id': 'tds', 
                'name': 'Towards Data Science', 
                'description': 'Artículos técnicos',
                'available': 'tds' in self.sources
            }
        ]
        
        return {'sources': sources}
    
    async def _process_medium(self, query: str) -> List[Dict[str, Any]]:
        """
        Procesa una consulta utilizando el agente de Medium.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de artículos encontrados en formato estandarizado
        """
        if not hasattr(self, 'medium_agent') or not self.medium_agent:
            logger.warning("El agente de Medium no está disponible")
            return []
            
        try:
            logger.info(f"Buscando en Medium: {query}")
            
            # Obtener resultados de Medium con manejo de errores
            try:
                results = self.medium_agent.search_articles(query=query, max_results=10)
                if not isinstance(results, list):
                    logger.warning("La respuesta de Medium no es una lista")
                    return []
            except Exception as e:
                logger.error(f"Error al obtener resultados de Medium: {str(e)}")
                return []
            
            processed_results = []
            for result in results:
                try:
                    if not isinstance(result, dict):
                        logger.warning(f"Resultado de Medium no es un diccionario: {result}")
                        continue
                        
                    # Extraer información básica con valores por defecto seguros
                    title = result.get('title', 'Sin título').strip()
                    summary = result.get('summary', '').strip()
                    
                    # Extraer la primera oración del resumen como descripción corta
                    abstract = summary.split('. ')[0] + '.' if summary else ""
                    
                    # Procesar autores
                    authors = []
                    if 'author' in result and result['author']:
                        if isinstance(result['author'], list):
                            authors = [{'name': str(author).strip()} for author in result['author'] if str(author).strip()]
                        elif isinstance(result['author'], str):
                            authors = [{'name': result['author'].strip()}]
                    
                    # Procesar categorías/etiquetas
                    categories = []
                    if 'tags' in result:
                        if isinstance(result['tags'], list):
                            categories = [str(tag).strip() for tag in result['tags'] if str(tag).strip()]
                        elif isinstance(result['tags'], str):
                            categories = [tag.strip() for tag in result['tags'].split(',') if tag.strip()]
                    
                    # Construir el resultado procesado
                    processed = {
                        'id': f"medium-{result.get('id', '').strip()}" if result.get('id') else f"medium-{hash(title)}",
                        'title': title,
                        'abstract': abstract,
                        'summary': summary,
                        'published': self._format_date(result.get('published')),
                        'authors': authors,
                        'categories': categories,
                        'primary_category': categories[0] if categories else '',
                        'url': result.get('url', '').strip(),
                        'source': 'Medium',
                        'relevance': self._calculate_relevance({
                            'title': title,
                            'abstract': summary
                        }, query)
                    }
                    
                    # Añadir campos opcionales
                    optional_fields = [
                        'read_time', 'claps', 'responses', 'publication',
                        'subtitle', 'reading_time', 'topics', 'language'
                    ]
                    for field in optional_fields:
                        if field in result and result[field] is not None:
                            processed[field] = result[field]
                    
                    # Asegurar que los campos numéricos sean del tipo correcto
                    for field in ['read_time', 'claps', 'responses']:
                        if field in processed and processed[field] is not None:
                            try:
                                processed[field] = int(processed[field])
                            except (ValueError, TypeError):
                                processed[field] = 0
                    
                    processed_results.append(processed)
                    
                except Exception as e:
                    logger.error(f"Error procesando resultado de Medium: {str(e)}", exc_info=True)
                    continue
            
            logger.info(f"Medium devolvió {len(processed_results)} resultados válidos de {len(results)} obtenidos")
            return processed_results
            
        except Exception as e:
            error_msg = f"Error en la búsqueda de Medium: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return []
