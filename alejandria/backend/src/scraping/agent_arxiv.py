"""
Agent for scraping ArXiv papers
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
import logging


class ArxivAgent:
    """
    Agent to scrape and process ArXiv papers
    """
    
    def __init__(self):
        self.base_url = "https://arxiv.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }

    def search_papers(self, query: str, max_results: int = 10, timeout: int = 30, type_query: str = "all", sortby: str = "relevance", sortorder: str = "descending", start: int = 0) -> List[Dict]:
        """
        Search ArXiv for papers matching the query (usando la API XML, no BeautifulSoup)
        """
        print(f"[ArxivAgent] Buscando papers para: '{query}'")
        try:
            # Construir URL de búsqueda usando la API XML de arXiv
            search_url = f"http://export.arxiv.org/api/query?search_query={type_query}:{query}&start={start}&max_results={max_results}&sortBy={sortby}&sortOrder={sortorder}"
            print(f"[ArxivAgent] URL de búsqueda: {search_url}")
            response = requests.get(
                search_url,
                headers=self.headers,
                timeout=timeout
            )
            response.raise_for_status()
            # Procesar respuesta XML con ElementTree (no BeautifulSoup)
            return self.parse_response(response.text)
        except requests.Timeout:
            print("[ArxivAgent] Timeout al conectar con ArXiv")
            return []
        except requests.RequestException as e:
            print(f"[ArxivAgent] Error en la petición a ArXiv: {str(e)}")
            return []
        except Exception as e:
            print(f"[ArxivAgent] Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def fetch_articles(self, query: str, max_results: int = 10, timeout: int = 30, type_query: str = "all", sortby: str = "relevance", sortorder: str = "descending", start: int = 0) -> List[Dict]:
        """
        Alias for search_papers to match the expected interface
        """
        return self.search_papers(query, max_results, timeout, type_query, sortby, sortorder, start)

    def parse_response(self, xml_data):
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        articles = []
        
        for entry in root.findall("atom:entry", ns):
            try:
                # Título
                title = entry.find("atom:title", ns).text.strip() if entry.find("atom:title", ns) is not None else "Sin título"
                
                # Autores
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns)
                    if name is not None and name.text:
                        authors.append(name.text.strip())
                authors = ", ".join(authors) if authors else "Autor desconocido"
                
                # Resumen
                summary = entry.find("atom:summary", ns).text.strip() if entry.find("atom:summary", ns) is not None else ""
                
                # Enlaces (PDF, DOI, etc.)
                pdf_url = ""
                doi = ""
                link_article = ""
                for link in entry.findall("atom:link", ns):
                    href = link.attrib.get("href", "")
                    if link.attrib.get("title") == "pdf" and link.attrib.get("type") == "application/pdf":
                        pdf_url = href
                    elif link.attrib.get("title") == "doi" or "doi.org" in href:
                        doi = href
                    if link.attrib.get("rel") == "alternate" and link.attrib.get("type") == "text/html":
                        link_article = href
                # Extraer enlaces de GitHub directamente de los links atom
                github_links = []
                github_link = ""
                if not github_links and summary:
                    from .agent_link_extractor import extract_github_links
                    github_links = extract_github_links(summary)
                github_link = github_links[0] if github_links else ""
                # Verificar estado del enlace de GitHub
                github_status = "No link"
                if github_link:
                    try:
                        github_link = github_link.rstrip(".,;:!?\"')")
                        import requests
                        r = requests.head(github_link, timeout=5, allow_redirects=True)
                        github_status = "OK" if r.status_code == 200 else "Broken"
                    except Exception as e:
                        logging.warning(f"Error verificando enlace GitHub {github_link}: {e}")
                        github_status = "Error"
                
                # Fecha de publicación
                published = entry.find("atom:published", ns).text.strip() if entry.find("atom:published", ns) is not None else ""
                
                # Crear diccionario del artículo
                article = {
                    "title": title,
                    "authors": authors,
                    "summary": summary,
                    "pdf_url": pdf_url,
                    "doi": doi,
                    "github_links": github_links,
                    "github_link": github_link,
                    "github_status": github_status,
                    "url": link_article,  # <-- asegúrate de incluir el link al portal
                    "published": published,  # <-- añade la fecha de publicación
                }
                articles.append(article)
            except Exception as e:
                logging.error(f"Error procesando entrada de arXiv: {e}", exc_info=True)
                continue
        return articles
