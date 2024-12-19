from serpapi import GoogleSearch
from scholarly import scholarly
import pandas as pd
from datetime import datetime


class GoogleScholarScraper:
    def __init__(self, method="scholarly", api_key=None):

        self.method = method.lower()
        self.api_key = api_key
        self.data = []

        if self.method == "serpapi" and not self.api_key:
            raise ValueError("Para usar SerpAPI, debes proporcionar una API Key.")

    def search_articles(self, query, max_results=10):
        if self.method == "serpapi":
            self._search_with_serpapi(query, max_results)
        elif self.method == "scholarly":
            self._search_with_scholarly(query, max_results)
        else:
            raise ValueError("Método inválido. Usa 'serpapi' o 'scholarly'.")

    def _search_with_serpapi(self, query, max_results):

        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": self.api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        # Extraer resultados
        articles = results.get("organic_results", [])
        count = 0

        for article in articles:
            if count >= max_results:
                break
            try:
                title = article.get("title", "N/A")
                summary = article.get("snippet", "N/A")
                authors = article.get("publication_info", {}).get("authors", "N/A")
                link_article = article.get("link", "N/A")
                published_date = article.get("publication_info", {}).get("published_date", "N/A")

                # Convertir fecha si existe
                if published_date and published_date != "N/A":
                    try:
                        published_date = datetime.strptime(published_date, "%Y")
                    except ValueError:
                        published_date = None
                else:
                    published_date = None

                self.data.append({
                    "published": published_date,
                    "title": title,
                    "summary": summary,
                    "authors": authors,
                    "link_article": link_article
                })
                count += 1
                print(f"SerpAPI - Artículo {count}: {title}")

            except Exception as e:
                print(f"Error en SerpAPI: {e}")
                continue

    def _search_with_scholarly(self, query, max_results):
        
        search_results = scholarly.search_pubs(query)
        count = 0

        for result in search_results:
            if count >= max_results:
                break
            try:
                title = result.get('bib', {}).get('title', 'N/A')
                summary = result.get('bib', {}).get('abstract', 'N/A')
                authors = ', '.join(result.get('bib', {}).get('author', []))
                link_article = result.get('pub_url', 'N/A')
                published = result.get('bib', {}).get('pub_year', 'N/A')

                # Convertir a formato compatible
                published_date = datetime(year=int(published), month=1, day=1) if published != 'N/A' else None

                self.data.append({
                    "published": published_date,
                    "title": title,
                    "summary": summary,
                    "authors": authors,
                    "link_article": link_article
                })
                count += 1
                print(f"Scholarly - Artículo {count}: {title}")

            except Exception as e:
                print(f"Error en scholarly: {e}")
                continue

    def get_dataframe(self):
        return pd.DataFrame(self.data)