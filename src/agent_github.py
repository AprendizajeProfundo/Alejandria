# agent_github.py
import requests
from config import GITHUB_API_URL, GITHUB_TOKEN

class GitHubAgent:
    def __init__(self, owner, repo):
        self.owner = owner
        self.repo = repo
        self.base_url = GITHUB_API_URL
        self.headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

    def fetch_readme(self):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/readme"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Error al recuperar el readme de GitHub: {response.status_code}")
        data = response.json()
        # El contenido viene codificado en base64
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content

    def fetch_repo_files(self, path=""):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Error al recuperar archivos del repositorio: {response.status_code}")
        return response.json()

# Ejecución de prueba
if __name__ == "__main__":
    agent = GitHubAgent("microsoft", "autogen")
    readme = agent.fetch_readme()
    files = agent.fetch_repo_files()
    print(readme)
    print("---------------------------------------------")
    print(files)
