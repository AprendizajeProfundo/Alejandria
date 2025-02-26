# agent_manager.py
import os
import time
import nbformat
import json
from agent_github import GitHubAgent
from notebook_generator import create_notebook_json  # (opcional, si lo usas)

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
        Si la propiedad "source" es una lista, la une en un solo string.
        Se espera que cell_dict tenga al menos las claves "cell_type" y "source".
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

    def run_pipeline_multi(self, selected_articles, github_mapping, notebook_json=None):
        """
        Procesa los artículos seleccionados para construir el notebook final.
        Si se proporciona notebook_json (un único JSON con la clave "cells"),
        se convierte directamente a NotebookNode; de lo contrario, se genera a partir
        de los resúmenes de cada artículo.
        """
        self.log_event("Iniciando pipeline de Alejandría para múltiples artículos.")
        combined_cells = []
        
        if notebook_json is not None and isinstance(notebook_json, dict) and "cells" in notebook_json:
            self.log_event("Se encontró un JSON unificado del agente de filtrado. Procesando sus celdas...")
            for cell_dict in notebook_json["cells"]:
                # Asegurarse de que cada celda sea un diccionario
                if not isinstance(cell_dict, dict):
                    try:
                        cell_dict = json.loads(cell_dict)
                    except Exception as e:
                        self.log_event(f"Error parseando celda: {e}")
                        continue
                combined_cells.append(self.convert_cell(cell_dict))
        else:
            # Fallback: usar resúmenes de cada artículo
            for article in selected_articles:
                self.log_event(f"No se proporcionó JSON unificado para {article['title']}; usando resumen.")
                combined_cells.append(nbformat.v4.new_markdown_cell("Resumen: " + article.get("summary", "")))
                # Integrar GitHub (opcional)
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

if __name__ == "__main__":
    # Prueba de AgentManager
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
    # Simulación: notebook_json es un JSON unificado ya generado, con la clave "cells"
    notebook_json = {
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
    manager = AgentManager()
    nb_json_result, logs = manager.run_pipeline_multi(sample_articles, github_mapping, notebook_json=notebook_json)
    print(json.dumps(nb_json_result, indent=2))
    for log in logs:
        print(log)
