# agent_link_extractor.py
import re

def extract_github_links(text):
    """
    Función placeholder para simular el uso de un modelo de IA que extraiga
    enlaces de GitHub del texto. Aquí se utiliza una expresión regular simple.
    """
    pattern = r"https?://github\.com/[\w\-]+/[\w\-.]+"
    links = re.findall(pattern, text)
    return list(set(links))