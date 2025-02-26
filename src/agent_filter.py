# agent_filter.py
import os
import re
import json
import PyPDF2
import requests
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

def extract_text_from_pdf(pdf_path):
    """Extrae todo el texto del PDF."""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text[:200]

def call_llm_for_sections(text, stream_placeholder=None):
    # Nuevo prompt que solicita que se genere un notebook válido según la estructura Jupyter
    system_prompt = (
        "Actúa como un ingeniero experto en generación de notebooks Jupyter TOTALMENTE EN ESPAÑOL. "
        "Dado el texto completo de un artículo científico, extrae las secciones clave EN ESPAÑOL (por ejemplo, Introducción, Metodología, Resultados, Conclusiones, etc.) y genera un JSON válido que represente un notebook de Jupyter, siguiendo EXACTAMENTE la siguiente estructura (sin nada adicional):\n\n"
        "{\n"
        " \"cells\": [\n"
        "    {\"cell_type\": \"markdown\", \"id\": \"<unique_id>\", \"metadata\": {}, \"source\": [\"<Contenido de la sección>\"]},\n"
        "    ...\n"
        " ],\n"
        " \"metadata\": {\n"
        "    \"kernelspec\": {\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"},\n"
        "    \"language_info\": {\"name\": \"python\", \"version\": \"3.x\"}\n"
        " },\n"
        " \"nbformat\": 4,\n"
        " \"nbformat_minor\": 5\n"
        "}\n\n"
        "Genera únicamente este JSON y nada más."
    )
    user_prompt = text

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": None,
        "n": 1,
        "temperature": 0,
        "stream": True
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    if stream_placeholder:
        stream_placeholder.text("Procesando prompt, espere por favor...")
    response = requests.post(LLM_BASE_URL + "/chat/completions", json=payload, headers=headers, stream=True)
    if response.status_code != 200:
        raise Exception(f"Error en la llamada al LLM: {response.status_code} {response.text}")
    
    full_output = ""
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("data:"):
                data_line = decoded_line[5:].strip()
                if data_line == "[DONE]":
                    break
                try:
                    data_json = json.loads(data_line)
                    if "choices" in data_json:
                        for choice in data_json["choices"]:
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                full_output += content
                                if stream_placeholder:
                                    stream_placeholder.text(full_output)
                except Exception as e:
                    continue
                    
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", full_output, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: extraer desde la primera "{" hasta la última "}"
        start_index = full_output.find("{")
        end_index = full_output.rfind("}")
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = full_output[start_index:end_index+1]
        else:
            json_str = "{}"
    try:
        result = json.loads(json_str)
    except Exception as e:
        result = {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    return result


def process_pdf(pdf_path, stream_placeholder=None):
    text = extract_text_from_pdf(pdf_path)
    result = call_llm_for_sections(text, stream_placeholder=stream_placeholder)
    return result

# Prueba (opcional)
if __name__ == "__main__":
    test_pdf = os.path.join("papers", "input", "example.pdf")
    if os.path.exists(test_pdf):
        res = process_pdf(test_pdf)
        print(json.dumps(res, indent=2))
    else:
        print("No se encontró el PDF de prueba.")
