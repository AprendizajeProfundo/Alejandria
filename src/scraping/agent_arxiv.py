# agent_arxiv.py
import re
import logging
import requests
import xml.etree.ElementTree as ET
from scraping.agent_link_extractor import extract_github_links
from scraping.config import ARXIV_API_URL, QUERY_TOPIC, TYPE_QUERY, START, MAX_RES, SORTBY, SORTORDER

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ArxivAgent:
    def __init__(self):
        self.base_url = ARXIV_API_URL

    def fetch_articles(self, type_query=TYPE_QUERY, query=QUERY_TOPIC, start=START, max_results=MAX_RES, sortby=SORTBY, sortorder=SORTORDER):
        url = self.base_url.format(type_query=type_query, query=query, start=start, max_results=max_results, sortby=sortby, sortorder=sortorder)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error al recuperar datos de Arxiv: {response.status_code}")
        articles = self.parse_response(response.text)
        return articles

    def parse_response(self, xml_data):
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        articles = []
        
        for entry in root.findall("atom:entry", ns):
            try:
                # ID y DOI
                arxiv_id = entry.find("atom:id", ns).text.strip() if entry.find("atom:id", ns) is not None else ""
                
                # Categorías
                categories = []
                primary_category = ""
                for cat in entry.findall("atom:category", ns):
                    term = cat.attrib.get("term", "")
                    if term:
                        categories.append(term)
                        if cat.attrib.get("scheme", "") == "http://arxiv.org/schemas/atom":
                            primary_category = term
                
                # Fechas
                published = entry.find("atom:published", ns).text.strip() if entry.find("atom:published", ns) is not None else ""
                updated = entry.find("atom:updated", ns).text.strip() if entry.find("atom:updated", ns) is not None else ""
                
                # Título, resumen y DOI
                title = entry.find("atom:title", ns).text.strip() if entry.find("atom:title", ns) is not None else ""
                summary = entry.find("atom:summary", ns).text.strip() if entry.find("atom:summary", ns) is not None else ""
                
                # Enlaces (PDF, DOI, etc.)
                pdf_url = ""
                doi = ""
                for link in entry.findall("atom:link", ns):
                    if link.attrib.get("title") == "pdf" and link.attrib.get("type") == "application/pdf":
                        pdf_url = link.attrib.get("href", "")
                    elif link.attrib.get("title") == "doi" or "doi.org" in link.attrib.get("href", ""):
                        doi = link.attrib.get("href", "")
                
                # Autores
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns).text.strip() if author.find("atom:name", ns) is not None else ""
                    if name:
                        authors.append({"name": name})
                
                # Link del artículo
                link_article = ""
                for link in entry.findall("atom:link", ns):
                    if link.attrib.get("rel") == "alternate" and link.attrib.get("type") == "text/html":
                        link_article = link.attrib.get("href", "")
                        break
                
                # Versión
                version = None
                m = re.search(r'v(\d+)$', link_article) if link_article else None
                if m:
                    version = m.group(1)
                
                # Extraer enlaces de GitHub
                github_links = extract_github_links(summary)
                github_link = github_links[0] if github_links else ""
                
                # Verificar estado del enlace de GitHub
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
                article = {
                    "id": arxiv_id,
                    "title": title,
                    "abstract": summary,
                    "published": published,
                    "updated": updated,
                    "authors": authors,
                    "categories": categories,
                    "primary_category": primary_category,
                    "doi": doi,
                    "url": link_article,
                    "pdf_url": pdf_url,
                    "github_links": github_links,
                    "github_link": github_link,
                    "github_status": github_status,
                    "version": version,
                    "source": "arXiv"
                }
                articles.append(article)
                
            except Exception as e:
                logging.error(f"Error procesando entrada de arXiv: {e}", exc_info=True)
                continue
                
        return articles

# Prueba de extracción
if __name__ == "__main__":
    import argparse

    # Definición de los argumentos de la línea de comandos
    parser = argparse.ArgumentParser(description="Consulta la API de arXiv y muestra resultados.")
    parser.add_argument("-q", "--query", type=str, default='RAG', 
                        help="Consulta para arXiv (p. ej., 'RAG+\"hybrid search\"')")
    parser.add_argument("--type_query", type=str, default=TYPE_QUERY, 
                        help="Tipo de consulta (según tu configuración)")
    parser.add_argument("--start", type=int, default=START, 
                        help="Índice de inicio para la paginación")
    parser.add_argument("--max_results", type=int, default=MAX_RES, 
                        help="Número máximo de resultados a obtener")
    parser.add_argument("--sortby", type=str, default=SORTBY, 
                        help="Criterio de ordenamiento (relevance, lastUpdatedDate, submittedDate)")
    parser.add_argument("--sortorder", type=str, default=SORTORDER, 
                        help="Orden de ordenamiento (ascending o descending)")
    
    args = parser.parse_args()

    # Creación del agente y llamada al método fetch_articles con los argumentos recibidos
    agent = ArxivAgent()
    articles = agent.fetch_articles(
        type_query=args.type_query,
        query=args.query,
        start=args.start,
        max_results=args.max_results,
        sortby=args.sortby,
        sortorder=args.sortorder
    )
    
    # Mostrar resultados
    for art in articles:
        print("\nTitle:", art["title"])
        print("Summary:", art["summary"])
        print("Authors:", art["authors"])
        print("Link:", art["link_article"])
        print("GitHub Link:", art["github_link"])
        print("GitHub Status:", art["github_status"])
        print("Published:", art["published"])
        print("---------------------------------------------")