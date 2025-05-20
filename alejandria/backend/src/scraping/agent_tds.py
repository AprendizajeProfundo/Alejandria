"""
Agent for scraping TDS (The Data Science) articles
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import logging
import random
import time
from urllib.parse import urljoin

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TdsAgent:
    """
    Agente para extraer artículos de Towards Data Science.
    """
    
    def __init__(self):
        """Inicializa el agente con configuración por defecto."""
        self.base_url = "https://towardsdatascience.com"
        self.search_url = f"{self.base_url}/search"
        self.session = requests.Session()
        self._setup_session()
        self.retry_attempts = 3
        self.retry_delay = 2  # segundos
    
    def _setup_session(self) -> None:
        """Configura la sesión con headers realistas."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def _get_random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Espera un tiempo aleatorio entre solicitudes."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Realiza una petición HTTP con manejo de reintentos.
        
        Args:
            url: URL a la que hacer la petición
            params: Parámetros de la URL
            
        Returns:
            Response object o None si hay un error
        """
        for attempt in range(self.retry_attempts):
            try:
                self._get_random_delay()
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    logger.error(f"Error en la petición a {url}: {str(e)}")
                    return None
                logger.warning(f"Reintentando ({attempt + 1}/{self.retry_attempts})...")
                time.sleep(self.retry_delay * (attempt + 1))
        return None

    def search_articles(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Busca artículos en Towards Data Science que coincidan con la consulta.
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de resultados a devolver
            
        Returns:
            Lista de diccionarios con la información de los artículos
        """
        if not query or not query.strip():
            logger.warning("La consulta de búsqueda está vacía")
            return []
            
        logger.info(f"Buscando en TDS: '{query}'")
        
        try:
            # Parámetros de búsqueda
            params = {
                'q': query,
                'source': 'search_post',
                'tagNames': 'data-science,machine-learning,artificial-intelligence,deep-learning,data-analysis',
            }
            
            # Realizar la petición
            response = self._make_request(self.search_url, params=params)
            if not response:
                logger.error("No se pudo obtener respuesta de TDS")
                return []
                
            # Parsear la respuesta
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontrar todos los artículos
            article_elements = soup.select('div.postArticle.postArticle--short')
            
            # Si no encontramos artículos, intentar con un selector alternativo
            if not article_elements:
                article_elements = soup.select('div.streamItem--postPreview')
                
            logger.info(f"Se encontraron {len(article_elements)} artículos en la página")
            
            # Procesar los artículos
            articles = []
            for element in article_elements:
                if len(articles) >= max_results:
                    break
                    
                try:
                    article = self._extract_article_data(element)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error procesando artículo: {str(e)}")
                    continue
            
            logger.info(f"Se procesaron {len(articles)} artículos correctamente")
            return articles
            
        except Exception as e:
            logger.error(f"Error en la búsqueda de TDS: {str(e)}")
            return []
    
    def _extract_article_data(self, element) -> Optional[Dict[str, Any]]:
        """
        Extrae los datos de un artículo a partir de un elemento HTML.
        
        Args:
            element: Elemento BeautifulSoup que contiene un artículo
            
        Returns:
            Diccionario con los datos del artículo o None si hay un error
        """
        try:
            # Extraer título y URL
            title_elem = element.select_one('h3')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title:
                return None
                
            url = self._extract_url(element)
            
            # Extraer resumen
            summary_elem = element.select_one('h4')
            summary = summary_elem.get_text(strip=True) if summary_elem else ""
            
            # Extraer autor
            author_elem = element.select_one('span[data-action="show-user-card"]')
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            # Extraer fecha de publicación
            published = self._extract_published_date(element)
            
            # Extraer etiquetas
            tags = self._extract_tags(element)
            
            # Extraer tiempo de lectura (opcional)
            read_time = self._extract_read_time(element)
            
            # Extraer número de aplausos (opcional)
            claps = self._extract_claps(element)
            
            return {
                "id": f"tds-{hash(url)}",
                "title": title,
                "url": url,
                "summary": summary,
                "author": author,
                "published": published,
                "tags": tags,
                "read_time": read_time,
                "claps": claps,
                "source": "Towards Data Science"
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo datos del artículo: {str(e)}")
            return None
    
    def _extract_url(self, element) -> str:
        """Extrae la URL del artículo."""
        link = element.select_one('a[data-action="open-post"]')
        if not link:
            link = element.select_one('a[data-action-value*="post"]')
        href = link.get('href', '') if link else ''
        return href if href.startswith('http') else urljoin(self.base_url, href)
    
    def _extract_published_date(self, element) -> str:
        """Extrae la fecha de publicación."""
        time_elem = element.select_one('time')
        if time_elem and 'datetime' in time_elem.attrs:
            return time_elem['datetime']
        return ""
    
    def _extract_tags(self, element) -> List[str]:
        """Extrae las etiquetas del artículo."""
        tags = []
        tag_elements = element.select('a[data-action="topic-link"]')
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text(strip=True)
            if tag_text and len(tag_text) > 1:  # Filtrar etiquetas vacías o de un solo carácter
                tags.append(tag_text)
        return tags
    
    def _extract_read_time(self, element) -> int:
        """Extrae el tiempo de lectura en minutos."""
        read_time_elem = element.select_one('span.readingTime')
        if read_time_elem and 'title' in read_time_elem.attrs:
            try:
                # Ejemplo: "4 min read" -> 4
                read_time_str = read_time_elem['title'].split()[0]
                return int(read_time_str)
            except (ValueError, IndexError):
                return 0
        return 0
    
    def _extract_claps(self, element) -> int:
        """Extrae la cantidad de aplausos."""
        claps_elem = element.select_one('button[data-action="show-recommends"]')
        if claps_elem:
            try:
                claps_text = claps_elem.get_text(strip=True)
                # Manejar formatos como "1.2K" o "500"
                if 'K' in claps_text:
                    return int(float(claps_text.replace('K', '')) * 1000)
                return int(claps_text) if claps_text.isdigit() else 0
            except (ValueError, AttributeError):
                return 0
        return 0

    def fetch_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Alias for search_articles to match the expected interface
        """
        return self.search_articles(query, max_results)
