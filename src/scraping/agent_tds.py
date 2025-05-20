# agent_tds.py
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import random
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TDSArticle:
    """Clase para representar un artículo de TDS"""
    title: str
    url: str
    summary: str = ""
    author: str = ""
    published: str = ""
    read_time: int = 0
    claps: int = 0
    tags: List[str] = None
    
    def to_dict(self) -> dict:
        """Convierte el artículo a diccionario"""
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "author": self.author,
            "published": self.published,
            "read_time": self.read_time,
            "claps": self.claps,
            "tags": self.tags or [],
            "source": "Towards Data Science"
        }

class TdsAgent:
    """
    Agent to scrape and process TDS articles with improved reliability
    """
    
    def __init__(self):
        self.base_url = "https://towardsdatascience.com"
        self.session = requests.Session()
        self._setup_session()
        self.retry_attempts = 3
        self.retry_delay = 2  # segundos
    
    def _setup_session(self):
        """Configura la sesión con headers realistas"""
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
        """Espera un tiempo aleatorio entre solicitudes"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """Realiza una petición HTTP con manejo de reintentos"""
        for attempt in range(self.retry_attempts):
            try:
                self._get_random_delay()
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    logger.error(f"Error en la petición a {url}: {str(e)}")
                    return None
                logger.warning(f"Reintentando ({attempt + 1}/{self.retry_attempts})...")
                time.sleep(self.retry_delay * (attempt + 1))
        return None

    def search_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search TDS for articles matching the query with improved reliability
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de resultados a devolver
            
        Returns:
            Lista de artículos encontrados
        """
        try:
            search_url = f"{self.base_url}/search"
            params = {
                'q': query,
                'source': 'search_post',
                'tagNames': 'data-science,machine-learning,artificial-intelligence,deep-learning,data-analysis',
            }
            
            logger.info(f"Buscando en TDS: {query}")
            response = self._make_request(search_url, params=params)
            if not response:
                return []
                
            # Parsear la respuesta
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontrar todos los artículos
            articles = []
            article_elements = soup.select('div.postArticle.postArticle--short')
            
            for element in article_elements[:max_results]:
                try:
                    article = TDSArticle(
                        title=self._extract_title(element),
                        url=self._extract_url(element),
                        summary=self._extract_summary(element),
                        author=self._extract_author(element),
                        published=self._extract_published_date(element),
                        read_time=self._extract_read_time(element),
                        claps=self._extract_claps(element),
                        tags=self._extract_tags(element)
                    )
                    articles.append(article.to_dict())
                except Exception as e:
                    logger.error(f"Error procesando artículo: {str(e)}")
                    continue
                    
            logger.info(f"Se encontraron {len(articles)} artículos en TDS")
            return articles
            
        except Exception as e:
            logger.error(f"Error en la búsqueda de TDS: {str(e)}")
            return []
    
    def _extract_title(self, element) -> str:
        """Extrae el título del artículo"""
        title_elem = element.select_one('h3')
        return title_elem.get_text(strip=True) if title_elem else "Sin título"
    
    def _extract_url(self, element) -> str:
        """Extrae la URL del artículo"""
        link = element.select_one('a[data-action="open-post"]')
        if not link:
            link = element.select_one('a[data-action-value*="post"]')
        href = link.get('href', '') if link else ''
        return href if href.startswith('http') else urljoin(self.base_url, href)
    
    def _extract_summary(self, element) -> str:
        """Extrae el resumen del artículo"""
        summary_elem = element.select_one('h4')
        return summary_elem.get_text(strip=True) if summary_elem else ""
    
    def _extract_author(self, element) -> str:
        """Extrae el nombre del autor"""
        author_elem = element.select_one('span[data-action="show-user-card"]')
        return author_elem.get_text(strip=True) if author_elem else ""
    
    def _extract_published_date(self, element) -> str:
        """Extrae la fecha de publicación"""
        time_elem = element.select_one('time')
        if time_elem and 'datetime' in time_elem.attrs:
            try:
                date_str = time_elem['datetime']
                # Convertir a formato estándar ISO
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.isoformat()
            except (ValueError, AttributeError):
                return ""
        return ""
    
    def _extract_read_time(self, element) -> int:
        """Extrae el tiempo de lectura en minutos"""
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
        """Extrae la cantidad de aplausos"""
        claps_elem = element.select_one('button[data-action="show-recommends"]')
        if claps_elem:
            try:
                claps_text = claps_elem.get_text(strip=True)
                # Manejar formatos como "1.2K" o "500"
                if 'K' in claps_text:
                    return int(float(claps_text.replace('K', '')) * 1000)
                return int(claps_text)
            except (ValueError, AttributeError):
                return 0
        return 0
    
    def _extract_tags(self, element) -> List[str]:
        """Extrae las etiquetas del artículo"""
        tags = []
        tag_elements = element.select('a[data-action="topic-link"]')
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text(strip=True)
            if tag_text and len(tag_text) > 1:  # Filtrar etiquetas vacías o de un solo carácter
                tags.append(tag_text)
        return tags
        posts = [li for li in soup.find_all("li") if li.get("class") and "wp-block-post" in li.get("class")]
        logging.debug(f"Encontrados {len(posts)} artículos en TDS.")

        for post in posts:
            try:
                # Extraer título y enlace
                title = ""
                url = ""
                h2 = post.find("h2", class_=lambda c: c and "wp-block-post-title" in c)
                if h2 and h2.find("a", href=True):
                    a_tag = h2.find("a")
                    title = a_tag.get_text(strip=True)
                    url = a_tag["href"]
                
                # Extraer resumen
                abstract = ""
                summary = post.find("div", class_=lambda c: c and "wp-block-post-excerpt" in c)
                if summary and summary.find("p"):
                    abstract = summary.find("p").get_text(strip=True)
                
                # Extraer categorías
                categories = []
                primary_category = ""
                cat_tag = post.find("a", class_=lambda c: c and "wp-block-tenup-post-primary-term" in c)
                if cat_tag:
                    primary_category = cat_tag.get_text(strip=True)
                    categories.append(primary_category)
                
                # Extraer fecha de publicación
                published = ""
                time_tag = post.find("time")
                if time_tag and time_tag.get("datetime"):
                    published = time_tag["datetime"]
                
                # Extraer autor
                authors = []
                author_tag = post.find("a", class_=lambda c: c and "wp-block-post-author" in c)
                if author_tag:
                    author_name = author_tag.get_text(strip=True)
                    if author_name:
                        authors.append({"name": author_name})
                
                # Extraer enlaces de GitHub
                github_links = extract_github_links(abstract)
                github_link = github_links[0] if github_links else ""
                github_status = "No link"
                
                if github_link:
                    try:
                        github_link = github_link.rstrip(".,;:!?\"')")
                        r = requests.head(github_link, timeout=5, allow_redirects=True)
                        github_status = "OK" if r.status_code == 200 else "Broken"
                    except Exception as e:
                        logging.warning(f"Error verificando enlace GitHub {github_link}: {e}")
                        github_status = "Error"
                
                # Construir el artículo
                article_id = f"tds-{hash(url) & 0xffffffff}" if url else f"tds-{hash(str(title)) & 0xffffffff}"
                article = {
                    "id": article_id,
                    "title": title,
                    "abstract": abstract,
                    "published": published,
                    "updated": published,  # TDS no siempre tiene updated separado
                    "authors": authors,
                    "categories": categories,
                    "primary_category": primary_category,
                    "url": url,
                    "github_links": github_links,
                    "github_link": github_link,
                    "github_status": github_status,
                    "source": "Towards Data Science"
                }
                articles.append(article)
                
            except Exception as e:
                logging.error(f"Error procesando artículo de TDS: {e}", exc_info=True)
                continue

            # Extraer la descripción desde el <div> con la clase wp-block-post-excerpt
            description = None
            excerpt_div = post.find("div", class_=lambda c: c and "wp-block-post-excerpt" in c)
            if excerpt_div:
                p_tag = excerpt_div.find("p", class_=lambda c: c and "wp-block-post-excerpt__excerpt" in c)
                if p_tag:
                    description = p_tag.get_text(strip=True)

            # Extraer el autor desde el <div> con la clase wp-block-post-author-name
            author = None
            author_div = post.find("div", class_=lambda c: c and "wp-block-post-author-name" in c)
            if author_div:
                a_author = author_div.find("a", href=True)
                if a_author:
                    author = a_author.get_text(strip=True)

            # Extraer la fecha desde el <div> con la clase wp-block-post-date
            date = None
            date_div = post.find("div", class_=lambda c: c and "wp-block-post-date" in c)
            if date_div:
                time_tag = date_div.find("time")
                if time_tag:
                    date = time_tag.get_text(strip=True)

            article = {
                "title": title,
                "link": link,
                "category": category,
                "description": description,
                "author": author,
                "date": date
            }
            articles.append(article)
        return articles

# Prueba de extracción
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Consulta la web de Towards Data Science y muestra resultados."
    )
    parser.add_argument(
        "-q", "--query", type=str, default=QUERY_TOPIC_TDS,
        help="Consulta para TDS (ej.: 'RAG' o 'machine+learning')"
    )
    args = parser.parse_args()

    agent = TdsAgent()
    articles = agent.fetch_articles(query=args.query)
    
    # Mostrar el resultado final en formato JSON
    print(json.dumps(articles, indent=2, ensure_ascii=False))
