"""
Agent for scraping GitHub repositories
"""

import requests
from typing import List, Dict, Optional


class GitHubAgent:
    """
    Agent to scrape and process GitHub repositories
    """
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }

    def search_repositories(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search GitHub for repositories matching the query
        """
        try:
            search_url = f"{self.base_url}/search/repositories?q={query}&sort=stars&order=desc"
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            for repo in data.get('items', [])[:max_results]:
                repositories.append({
                    'title': f"{repo['name']} by {repo['owner']['login']}",
                    'description': repo['description'] or "No description available",
                    'summary': f"{repo['description'] or 'No description available'}\n\n"
                              f"⭐ {repo['stargazers_count']} stars | 🍴 {repo['forks_count']} forks\n"
                              f"🌐 {repo['html_url']}",
                    'link': repo['html_url'],
                    'source': 'GitHub',
                    'type': 'code',
                    'language': repo.get('language', 'N/A'),
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count']
                })
            
            return repositories
            
        except requests.RequestException as e:
            print(f"Error searching GitHub: {e}")
            return []
    
    def fetch_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Alias for search_repositories to match the expected interface
        """
        return self.search_repositories(query, max_results)
