# agent_arxiv.py
import re
import requests
import xml.etree.ElementTree as ET
from agent_link_extractor import extract_github_links
from config import ARXIV_API_URL, QUERY_TOPIC, TYPE_QUERY, START, MAX_RES, SORTBY, SORTORDER

class ArxivAgent:
    def __init__(self):
        self.base_url = ARXIV_API_URL

    def fetch_articles(self, type_query=TYPE_QUERY, query=QUERY_TOPIC, start=START, max_results=MAX_RES, sortby=SORTBY, sortorder=SORTORDER):
        url = self.base_url.format(query=query, start=start, max_results=max_results, sortby=sortby, sortorder=sortorder, type_query=type_query)
        response = requests.get(url)
        #print(response.content)
        if response.status_code != 200:
            raise Exception(f"Error al recuperar datos de Arxiv: {response.status_code}")
        articles = self.parse_response(response.text)
        return articles

    def parse_response(self, xml_data):
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        articles = []
        for entry in root.findall("atom:entry", ns):
            # Categoría primaria
            primary_category = ""
            primary_cat_elem = entry.find("arxiv:primary_category", ns)
            if primary_cat_elem is not None:
                primary_category = primary_cat_elem.attrib.get("term", "")
            # Fechas
            published = entry.find("atom:published", ns).text.strip() if entry.find("atom:published", ns) is not None else ""
            updated = entry.find("atom:updated", ns).text.strip() if entry.find("atom:updated", ns) is not None else ""
            # Título y resumen
            title = entry.find("atom:title", ns).text.strip() if entry.find("atom:title", ns) is not None else ""
            summary = entry.find("atom:summary", ns).text.strip() if entry.find("atom:summary", ns) is not None else ""
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                # Se busca el link cuyo atributo title sea "pdf" y type sea "application/pdf"
                if link.attrib.get("title") == "pdf" and link.attrib.get("type") == "application/pdf":
                    pdf_url = link.attrib.get("href", "")
                    break
            # Autores (lista de diccionarios)
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text.strip() if author.find("atom:name", ns) is not None else ""
                authors.append({"name": name})
            # Link del artículo (se toma el primero con rel="alternate")
            link_article = ""
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("rel") == "alternate":
                    link_article = link.attrib.get("href", "")
                    break
            # Versión: se extrae del link_article (p.ej. ...v1, ...v2, etc.)
            version = None
            m = re.search(r'v(\d+)$', link_article)
            if m:
                version = m.group(1)
            # Extracción de enlaces GitHub a partir del resumen
            github_links = extract_github_links(summary)
            # Si hay algún link, limpiamos el primero quitándole caracteres de puntuación final
            github_link = None
            github_status = "No link"
            if github_links and len(github_links) > 0:
                raw_link = github_links[0]
                # Quitar puntos, comas, dos puntos o espacios finales
                github_link = raw_link.rstrip(".,;:! ")
                try:
                    # Usamos GET en modo streaming para seguir redirecciones
                    r = requests.get(github_link, timeout=5, stream=True)
                    if r.status_code == 200:
                        github_status = "OK"
                    else:
                        github_status = "Broken"
                except Exception:
                    github_status = "Broken"
            article = {
                "title": title,
                "published": published,
                "summary": summary,
                "primary_category": primary_category,
                "updated": updated,
                "authors": authors,
                "link_article": link_article,  # usaremos este valor como id único
                "github_links": github_links,   # lista original
                "github_link": github_link,     # primer link limpio (si existe)
                "github_status": github_status,
                "version": version,
                "pdf_link": pdf_url
            }
            articles.append(article)
        return articles

# Prueba de extracción
if __name__ == "__main__":
    agent = ArxivAgent()
    articles = agent.fetch_articles(query="RAG")
    for art in articles:
        print("\nTitle:", art["title"])
        print("Summary:", art["summary"])
        print("Authors:", art["authors"])
        print("Link:", art["link_article"])
        print("GitHub Link:", art["github_link"])
        print("GitHub Status:", art["github_status"])
        print("Published:", art["published"])
        print("---------------------------------------------")
