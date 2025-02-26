# agent_manager.py
import os
import time
import nbformat
from agent_github import GitHubAgent
from notebook_generator import create_notebook_json

def download_pdf(pdf_url, output_folder, filename):
    """
    Descarga el PDF desde pdf_url y lo guarda en output_folder con el nombre filename.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, filename)
    import requests
    response = requests.get(pdf_url, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path
    else:
        raise Exception(f"Error descargando PDF: {response.status_code}")

class AgentManager:
    def __init__(self):
        self.log = []

    def log_event(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log.append(log_message)
        return log_message

    def convert_cell(self, cell_dict):
        """
        Convierte un diccionario que representa una celda en un objeto NotebookNode.
        Si la propiedad "source" es una lista, se une en un solo string.
        Se espera que cell_dict tenga al menos la clave "cell_type" y "source".
        """
        source = cell_dict.get("source", "")
        if isinstance(source, list):
            source = "\n".join(source)
        if cell_dict.get("cell_type") == "code":
            cell = nbformat.v4.new_code_cell(source)
        else:
            cell = nbformat.v4.new_markdown_cell(source)
        if "metadata" in cell_dict:
            cell.metadata = cell_dict["metadata"]
        if "id" in cell_dict:
            cell.id = cell_dict["id"]
        return cell

    def run_pipeline_multi(self, selected_articles, github_mapping, pdf_results=None):
        """
        Procesa los artículos seleccionados:
         - Si existe en pdf_results un JSON con la estructura del notebook, se extraen sus "cells"
           y se convierten a NotebookNode; de lo contrario, se usa el resumen como celda markdown.
         - Se integra opcionalmente el contenido de GitHub.
         - Se construye un notebook consolidado y se retorna junto con los logs.
        """
        self.log_event("Iniciando pipeline de Alejandría para múltiples artículos.")
        combined_cells = []
        
        for article in selected_articles:
            self.log_event(f"Procesando artículo: {article['title']}")
            if pdf_results and article["link_article"] in pdf_results:
                article_notebook = pdf_results.get(article["link_article"])
                if article_notebook and "cells" in article_notebook and article_notebook["cells"]:
                    num_cells = len(article_notebook["cells"])
                    self.log_event(f"Integradas {num_cells} celdas del artículo {article['title']}.")
                    for cell_dict in article_notebook["cells"]:
                        combined_cells.append(self.convert_cell(cell_dict))
                else:
                    self.log_event(f"No se encontraron celdas en el JSON extraído para {article['title']}, usando resumen.")
                    combined_cells.append(nbformat.v4.new_markdown_cell("Resumen: " + article.get("summary", "")))
            else:
                self.log_event(f"No se extrajo notebook para {article['title']}, usando resumen.")
                combined_cells.append(nbformat.v4.new_markdown_cell("Resumen: " + article.get("summary", "")))
            
            chosen_github = github_mapping.get(article["link_article"].rstrip("/"))
            if chosen_github:
                try:
                    self.log_event(f"Recuperando contenido de GitHub para {article['title']} desde {chosen_github}...")
                    owner, repo = self.parse_github_link(chosen_github)
                    gh_agent = GitHubAgent(owner, repo)
                    github_readme = gh_agent.fetch_readme()
                    combined_cells.append(nbformat.v4.new_markdown_cell(github_readme))
                    self.log_event("Contenido de GitHub integrado correctamente.")
                except Exception as e:
                    self.log_event(f"Error al recuperar contenido de GitHub para {article['title']}: {e}")
            else:
                self.log_event(f"No se integró repositorio GitHub para {article['title']}.")
        
        self.log_event("Construyendo notebook consolidado...")
        nb = nbformat.v4.new_notebook()
        nb.cells = combined_cells
        nb.metadata = {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.x"
            }
        }
        nb.nbformat = 4
        nb.nbformat_minor = 5
        self.log_event("Notebook consolidado construido.")
        self.log_event("Pipeline completado.")
        return nb, self.log

    def parse_github_link(self, link):
        parts = link.rstrip('/').split('/')
        if len(parts) >= 5:
            owner = parts[-2]
            repo = parts[-1]
            return owner, repo
        return None, None

# Prueba de AgentManager (para testeo independiente)
if __name__ == "__main__":
    sample_articles = [{
        "title": "Artículo de Ejemplo",
        "published": "2020-01-01T00:00:00Z",
        "updated": "2020-01-01T00:00:00Z",
        "summary": "Resumen de ejemplo con link https://github.com/octocat/Hello-World.",
        "authors": [{"name": "Autor Ejemplo"}],
        "link_article": "http://arxiv.org/abs/0000.0000v1",
        "pdf_url": "http://arxiv.org/pdf/0000.0000v1.pdf",
        "github_links": ["https://github.com/octocat/Hello-World"],
        "github_link": "https://github.com/octocat/Hello-World",
        "github_status": "OK",
    }]
    github_mapping = {"http://arxiv.org/abs/0000.0000v1": "https://github.com/octocat/Hello-World"}
    pdf_results = {
        "http://arxiv.org/abs/0000.0000v1": {
            "cells": [
                {
                    "cell_type": "markdown",
                    "id": "abc123",
                    "metadata": {},
                    "source": [
                        "### Artículo de Ejemplo\n\nContenido extraído del paper en español."
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3 (ipykernel)",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.x"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
    }
    manager = AgentManager()
    nb_json, logs = manager.run_pipeline_multi(sample_articles, github_mapping, pdf_results=pdf_results)
    print(nb_json)
    for log in logs:
        print(log)
