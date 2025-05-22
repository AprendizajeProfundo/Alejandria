import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from typing import Annotated
import PyPDF2
import io

class ArxivScraper:

    def __init__(self):

        self.url = r'http://export.arxiv.org/api/query?search_query={type_query}:{query}&start={start}&max_results={max_results}&sortBy={sortby}&sortOrder={sortorder}'


    def fetch_html(
        self,
        query: str,
        type_query: str,
        start: int,
        max_results: int, 
        sortby: str,
        sortorder: str
    ) -> str:
        """
        Realiza una solicitud HTTP GET usando urllib y devuelve el contenido HTML.
        """
        arxiv_url = self.url.format(query=query, type_query=type_query, start=start, max_results=max_results, sortby=sortby, sortorder=sortorder)
        print(arxiv_url)

        try:
            # Realizar la solicitud
            data = requests.get(arxiv_url)
            # Leer y decodificar el contenido
            html = data.text
            return html
        except Exception as e:
            # Manejo básico de errores
            return f"Error al hacer la solicitud: {str(e)}"
        
    def get_metadata(self, html_content: str):
        soup = BeautifulSoup(html_content, "lxml-xml")
        articles = soup.find_all("entry")

        data_json = []
        for entry in articles:
            prim_category = entry.find("primary_category").get("term")
            published = entry.find("published").text
            updated = entry.find("updated").text
            title = entry.find("title").text
            summary = entry.find("summary").text
            authors = entry.find_all("author")
            authors = [auth.find("name").text for auth in authors]
            link_article = entry.select('link[title="pdf"]')[0].get("href")
            data_json.append({"primary_category": prim_category, 
                            "published": published,
                            "updated": updated,
                            "title": title, 
                            "summary": summary,
                            "authors": authors, 
                            "link_article": link_article})
            
        return data_json
    
    @staticmethod
    def json_to_df(data_json):
    
        data_df = pd.DataFrame.from_dict(data_json)
        columns_to_convert = ['published', 'updated']
        data_df[columns_to_convert] = data_df[columns_to_convert].apply(pd.to_datetime)
        data_df.insert(0, "id", data_df["link_article"].str.split(".").str[-1].str.replace("v*","", regex=True))
        data_df["id"] = data_df["id"].astype("int")
        data_df.insert(1, "version", data_df["link_article"].str.split(".").str[-1].str.split("v").str[-1])
        data_df.info()
        data_df.sort_values(by="published", ascending=False)

        return data_df
    
    def metadata_from_url(self, query, type_query, start, max_results, sortby, sortorder):
        
        html_content = self.fetch_html(query, type_query, start, max_results, sortby, sortorder)
        data_json = self.get_metadata(html_content)
        
        self.metadata_df = self.json_to_df(data_json)

    @staticmethod
    def download_pdf(pdf_url):
        try:
            # Solicitar el PDF desde la URL
            response = requests.get(pdf_url)
            response.raise_for_status()  # Asegurarse de que la descarga sea exitosa
            
            # Leer el contenido del PDF
            pdf_stream = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_stream)
            
            # Extraer texto del PDF página por página
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""  # Manejar páginas sin texto
            
            return text
        
        except Exception as e:
            print(f"Error descargando o procesando el PDF: {e}")
            return None
        
    def scrape_article(self, pdf_url, metadata):

        content = self.download_pdf(pdf_url)
        if content:
            self.metadata.append(metadata)
            self.pdf_contents[metadata['title']] = content
            print(f"PDF de '{metadata['title']}' descargado y procesado.")
        else:
            print(f"No se pudo procesar el PDF de '{metadata['title']}'.")
