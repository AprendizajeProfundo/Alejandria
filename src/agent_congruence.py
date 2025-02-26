# agent_congruence.py
import json
import requests
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
import re

def call_llm_for_congruence(summaries, stream_placeholder=None):
    """
    Dado un diccionario de resúmenes de cada artículo (con claves: paper_id y valores JSON),
    llama al LLM para evaluar la congruencia entre ellos y retorna un JSON con:
      {
         "related": <true/false>,
         "conclusion": "<Resumen consolidado del material educativo>",
         "details": "<Una frase que explica la relación>"
      }
    """
    # Preparar el prompt
    prompt_text = "Actúa como un experto en análisis de papers para material educativo. " \
                  "A continuación se presentan los resúmenes pedagógicos extraídos de varios artículos, " \
                  "donde cada resumen está en formato JSON y contiene claves como 'main_ideas', 'methods', " \
                  "'comparisons', 'algorithms' y 'other'. " \
                  "Analiza si los artículos tratan sobre el mismo tema (por ejemplo, agrupamiento) y " \
                  "si se pueden unir para formar un material educativo que explique el tema general y sus técnicas " \
                  "específicas. " \
                  "Genera únicamente un JSON con la siguiente estructura EXACTA:\n\n" \
                  "{\n" \
                  "  \"related\": <true/false>,\n" \
                  "  \"conclusion\": \"<Resumen consolidado del material educativo>\",\n" \
                  "  \"details\": \"<Una frase que explica la relación entre los artículos>\"\n" \
                  "}\n\n" \
                  "A continuación se presentan los resúmenes de los artículos:\n"
    for paper_id, summary in summaries.items():
        prompt_text += f"\n---\nPaper ID: {paper_id}\nResumen: {json.dumps(summary)}\n"
        print(prompt_text)
    prompt_text += "\n---\nGenera únicamente el JSON solicitado."

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Eres un experto en análisis de papers para material educativo."},
            {"role": "user", "content": prompt_text}
        ],
        "max_tokens": 1000,
        "n": 1,
        "temperature": 0,
        "stream": True
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    if stream_placeholder:
        stream_placeholder.text("Procesando congruencia, espere por favor...")
    response = requests.post(LLM_BASE_URL + "/chat/completions", json=payload, headers=headers, stream=True)
    if response.status_code != 200:
        raise Exception(f"Error en la llamada al LLM para congruencia: {response.status_code} {response.text}")

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
                    continue
    # Extraer bloque JSON delimitado por backticks o desde la primera { hasta la última }
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", full_output, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        start_index = full_output.find("{")
        end_index = full_output.rfind("}")
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = full_output[start_index:end_index+1]
        else:
            json_str = "{}"
    try:
        result = json.loads(json_str)
    except:
        result = {"related": False, "conclusion": "", "details": ""}
    return result

def check_congruence(summaries, stream_placeholder=None):
    return call_llm_for_congruence(summaries, stream_placeholder=stream_placeholder)

# Prueba (opcional)
if __name__ == "__main__":
    summaries = {
        "paper1": {"main_ideas": ["agrupamiento", "k-means"], "methods": ["algoritmo k-means"], "comparisons": [], "algorithms": ["k-means"], "other": []},
        "paper2": {"main_ideas": ["agrupamiento", "hdbscan"], "methods": ["hdbscan"], "comparisons": [], "algorithms": ["hdbscan"], "other": []}
    }
    result = check_congruence(summaries)
    print(json.dumps(result, indent=2))
