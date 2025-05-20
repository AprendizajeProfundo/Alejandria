"""
Agent for scraping ArXiv papers
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


class ArxivAgent:
    """
    Agent to scrape and process ArXiv papers
    """
    
    def __init__(self):
        self.base_url = "https://arxiv.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }

    def search_papers(self, query: str, max_results: int = 10, timeout: int = 30) -> List[Dict]:
        """
        Search ArXiv for papers matching the query
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            timeout: Request timeout in seconds
            
        Returns:
            List of paper dictionaries with metadata
        """
        print(f"[ArxivAgent] Buscando papers para: '{query}'")
        
        try:
            # Construir URL de búsqueda
            search_url = f"{self.base_url}/search/?query={query}&searchtype=all"
            print(f"[ArxivAgent] URL de búsqueda: {search_url}")
            
            # Realizar la petición con timeout
            response = requests.get(
                search_url, 
                headers=self.headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Analizar el HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            paper_elements = soup.find_all('li', class_='arxiv-result')[:max_results]
            print(f"[ArxivAgent] Encontrados {len(paper_elements)} papers")
            
            papers = []
            
            # Procesar cada paper encontrado
            for paper in paper_elements:
                try:
                    title_elem = paper.find('p', class_='title')
                    authors_elem = paper.find('p', class_='authors')
                    abstract_elem = paper.find('p', class_='abstract')
                    link_elem = paper.find('p', class_='list-title')
                    
                    # Extraer datos con manejo de errores
                    title = title_elem.text.strip() if title_elem else "Sin título"
                    authors = authors_elem.text.strip() if authors_elem else "Autor desconocido"
                    abstract = abstract_elem.text.strip() if abstract_elem else "Resumen no disponible"
                    
                    # Manejar enlace
                    link = "#"
                    if link_elem and link_elem.find('a'):
                        link = link_elem.find('a')['href']
                        if not link.startswith('http'):
                            link = f"{self.base_url}{link}"
                    
                    # Crear diccionario del paper
                    paper_data = {
                        'title': title,
                        'authors': authors,
                        'summary': abstract,
                        'link': link,
                        'source': 'ArXiv',
                        'type': 'academic',
                        'main_topics': query.split()[:3]  # Usar las primeras palabras de la consulta como temas
                    }
                    
                    papers.append(paper_data)
                    
                except Exception as e:
                    print(f"[ArxivAgent] Error procesando un paper: {str(e)}")
                    continue
            
            print(f"[ArxivAgent] Búsqueda completada. {len(papers)} papers procesados")
            return papers
            
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
    
    def fetch_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Alias for search_papers to match the expected interface
        """
        return self.search_papers(query, max_results)
