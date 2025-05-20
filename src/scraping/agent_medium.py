"""
Módulo para interactuar con la API de Medium a través de RapidAPI.
"""
import os
from typing import List, Dict, Optional
import requests
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediumAgent:
    """
    Agente para interactuar con la API de Medium a través de RapidAPI.
    
    Requiere una API key de RapidAPI con acceso a la API de Medium.
    """
    
    def __init__(self, api_key: str = None):
        """
        Inicializa el agente de Medium.
        
        Args:
            api_key: Clave de API de RapidAPI. Si no se proporciona, se buscará en la variable de entorno MEDIUM_API_KEY.
        """
        self.base_url = "https://medium2.p.rapidapi.com"
        self.api_key = api_key or os.getenv("MEDIUM_API_KEY")
        
        if not self.api_key:
            logger.warning("No se proporcionó una API key para Medium. Las búsquedas en Medium no funcionarán.")
        
        self.session = requests.Session()
        self._setup_session()
        self.retry_attempts = 3
        self.retry_delay = 2  # segundos
    
    def _setup_session(self) -> None:
        """Configura la sesión con los headers necesarios para la API de RapidAPI."""
        self.session.headers.update({
            'x-rapidapi-host': 'medium2.p.rapidapi.com',
            'x-rapidapi-key': self.api_key or '',
            'content-type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[dict]:
        """
        Realiza una petición a la API de Medium con manejo de errores y reintentos.
        
        Args:
            endpoint: Endpoint de la API a consultar (sin el base_url)
            method: Método HTTP (GET, POST, etc.)
            **kwargs: Argumentos adicionales para la petición
            
        Returns:
            Respuesta de la API como diccionario, o None si hay un error
        """
        if not self.api_key:
            logger.error("No se configuró una API key para Medium")
            return None
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    logger.error(f"Error en la petición a {url}: {str(e)}")
                    if hasattr(e, 'response') and e.response is not None:
                        logger.error(f"Respuesta del servidor: {e.response.text}")
                    return None
                logger.warning(f"Reintentando ({attempt + 1}/{self.retry_attempts})...")
                import time
                time.sleep(self.retry_delay * (attempt + 1))
        return None
    
    def search_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Busca artículos en Medium que coincidan con la consulta.
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de resultados a devolver (máx. 100)
            
        Returns:
            Lista de diccionarios con la información de los artículos
        """
        if not self.api_key:
            logger.warning("No se puede buscar en Medium: falta la API key")
            return []
            
        logger.info(f"Buscando en Medium: {query}")
        
        try:
            # La API de RapidAPI para Medium tiene un límite de 100 resultados por página
            page_size = min(max_results, 100)
            
            params = {
                'query': query,
                'page': '1',
                'pageSize': str(page_size)
            }
            
            data = self._make_request("/search/posts", params=params)
            if not data or 'data' not in data:
                logger.error("Respuesta inesperada de la API de Medium")
                return []
            
            articles = []
            for item in data['data'][:max_results]:
                try:
                    # Extraer la información relevante de cada artículo
                    article = {
                        'id': f"medium-{item.get('id', '')}",
                        'title': item.get('title', 'Sin título'),
                        'url': item.get('url', ''),
                        'summary': item.get('subtitle', ''),
                        'author': item.get('author', {}).get('name', ''),
                        'published': item.get('publishedAt', ''),
                        'read_time': item.get('readTime', 0),
                        'claps': item.get('claps', 0),
                        'tags': [tag.get('name', '') for tag in item.get('tags', [])],
                        'source': 'Medium',
                        'word_count': item.get('wordCount', 0),
                        'responses_count': item.get('responsesCount', 0),
                        'vocal_url': item.get('vocalUrl', '')
                    }
                    
                    # Procesar la fecha de publicación
                    if article['published']:
                        try:
                            # Convertir de timestamp a ISO format
                            dt = datetime.utcfromtimestamp(article['published'] / 1000)
                            article['published'] = dt.isoformat()
                        except (ValueError, TypeError):
                            article['published'] = ''
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error procesando artículo de Medium: {str(e)}")
                    continue
            
            logger.info(f"Se encontraron {len(articles)} artículos en Medium")
            return articles
            
        except Exception as e:
            logger.error(f"Error en la búsqueda de Medium: {str(e)}")
            return []
    
    def get_article_content(self, article_id: str) -> Optional[Dict]:
        """
        Obtiene el contenido completo de un artículo por su ID.
        
        Args:
            article_id: ID del artículo (sin el prefijo 'medium-')
            
        Returns:
            Diccionario con el contenido del artículo, o None si hay un error
        """
        if not self.api_key:
            logger.warning("No se puede obtener el artículo: falta la API key")
            return None
            
        logger.info(f"Obteniendo contenido del artículo {article_id}")
        
        try:
            data = self._make_request(f"/article/{article_id}")
            if not data:
                return None
                
            # Procesar la respuesta para extraer el contenido
            content = {
                'id': f"medium-{data.get('id', '')}",
                'title': data.get('title', ''),
                'content': data.get('content', ''),
                'url': data.get('url', ''),
                'author': data.get('author', {}).get('name', ''),
                'published': data.get('publishedAt', ''),
                'read_time': data.get('readTime', 0),
                'word_count': data.get('wordCount', 0),
                'tags': [tag.get('name', '') for tag in data.get('tags', [])]
            }
            
            # Procesar la fecha de publicación
            if content['published']:
                try:
                    dt = datetime.utcfromtimestamp(content['published'] / 1000)
                    content['published'] = dt.isoformat()
                except (ValueError, TypeError):
                    content['published'] = ''
            
            return content
            
        except Exception as e:
            logger.error(f"Error al obtener el artículo {article_id}: {str(e)}")
            return None

# Ejemplo de uso
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Cargar variables de entorno desde .env
    load_dotenv()
    
    # Inicializar el agente con la API key de las variables de entorno
    agent = MediumAgent(os.getenv("MEDIUM_API_KEY"))
    
    # Ejemplo de búsqueda
    results = agent.search_articles("machine learning", max_results=5)
    for i, article in enumerate(results, 1):
        print(f"\nArtículo {i}: {article['title']}")
        print(f"Autor: {article['author']}")
        print(f"URL: {article['url']}")
        print(f"Publicado: {article['published']}")
        print(f"Tiempo de lectura: {article['read_time']} min")
        print(f"Aplausos: {article['claps']}")
        print(f"Etiquetas: {', '.join(article['tags'])}")
