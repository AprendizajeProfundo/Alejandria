# agent_summarizer.py

import re
import requests
import json
import PyPDF2
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

def extract_full_text_from_pdf(pdf_path):
    """
    Extrae todo el texto del PDF.
    """
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text[:20000]

def call_llm_for_summary(text, stream_placeholder=None):
    """
    Llama al LLM para extraer un resumen pedagógico del artículo:
      - ideas principales
      - metodologías
      - comparaciones
      - algoritmos
      etc.
    Retorna un dict con las claves: 'main_ideas', 'methods', 'comparisons', 'algorithms', 'other'.
    
    Se utiliza el parámetro stream_placeholder para actualizar el progreso en streaming.
    """
    system_prompt = (
        "Actúa como un experto en análisis pedagógico de papers. "
        "Dado el texto de un artículo científico, extrae las secciones clave EN ESPAÑOL: "
        "ideas principales, metodologías, comparaciones, algoritmos, etc. "
        "Retorna tu respuesta en formato JSON con las claves: "
        "{ 'main_ideas': [...], 'methods': [...], 'comparisons': [...], 'algorithms': [...], 'other': [...] } "
        "Sin nada adicional."
    )
    user_prompt = text

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1500,
        "n": 1,
        "temperature": 0,
        "stream": True
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

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
                except:
                    pass
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
        result = {
            "main_ideas": [],
            "methods": [],
            "comparisons": [],
            "algorithms": [],
            "other": []
        }
    return result

def summarize_pdf(pdf_path, stream_placeholder=None):
    """
    Extrae el texto completo del PDF y llama al LLM para obtener el resumen pedagógico.
    """
    text = extract_full_text_from_pdf(pdf_path)
    summary = call_llm_for_summary(text, stream_placeholder=stream_placeholder)
    return summary

# Prueba (opcional)
if __name__ == "__main__":
    test_pdf = "papers/input/example.pdf"
    res = summarize_pdf(test_pdf)
    print(json.dumps(res, indent=2))
