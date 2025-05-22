# agent_filter.py
import os
import re
import json
import requests
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL_OPENAI, LLM_API_KEY_OPENAI, LLM_MODEL_OPENAI 

def call_llm_for_sections(text, stream_placeholder=None):
    """
    Llama al LLM para generar un notebook Jupyter en JSON, siguiendo EXACTAMENTE la siguiente estructura:
    
    {
      "cells": [
        {
          "cell_type": "markdown",
          "id": "<unique_id>",
          "metadata": {},
          "source": ["<Contenido de la sección>"]
        },
        {
          "cell_type": "code",
          "execution_count": null,
          "id": "<unique_id>",
          "metadata": {},
          "outputs": [],
          "source": ["<Código de ejemplo>"]
        },
        ...
      ],
      "metadata": {
        "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"}
      },
      "nbformat": 4,
      "nbformat_minor": 5
    }
    
    El LLM debe generar únicamente este JSON y nada más.
    """
    system_prompt = (
        "Actúa como un ingeniero experto en generación de notebooks Jupyter TOTALMENTE EN ESPAÑOL. "
        "Dado el siguiente texto que consolida información pedagógica sobre un tema en específico y varios textos asociados, "
        "genera un JSON válido que represente un notebook de Jupyter, y que pueda ser usado como material educativo de autoaprendizaje,"
        "incluyendo secciones de introducción, tabla de contenido, descripción detallada de cada método, comparaciones, conclusiones y un ejemplo de código, "
        "El JSON debe incluir celdas de markdown y celdas de código. Para las celdas de código, "
        "asegúrate de incluir la propiedad 'execution_count' con valor null y 'outputs' como una lista vacía. "
        "Si ves conceptos que se pueden generar en código pero real desde tu base de conocimiento, hazlo en las celdas de códigos correspondientes. PON EJEMPLOS REALES QUE APUNTEN AL TEMA. SE AMPLIO EN EL CÓDIGO."
        "También genera visualizaciones gráficas, para ejemplicar el tema o los reusltados. del código, con matplotlib o seaborn."
        "MUY IMPORTATNTE QUE HAGAS GRAFICOS PARA QUE ACOMPAÑEN EL CÓDIGO."
        "IMPORTANTE: Para las celdas de código que generen gráficos con matplotlib o seaborn, incluye la línea '%matplotlib inline' al principio de la celda (solo la primera vez que se use). "
        "NO uses plt.show(). Simplemente termina la celda con la instrucción de la figura (por ejemplo, plt.plot(...) o plt.figure(...)), para que el gráfico se muestre automáticamente en Jupyter."
        "Sigue EXACTAMENTE la siguiente estructura cuando se pueda seguir markdown y luego código o sólo markdown o solo código (sin nada adicional):\n\n"
        "{\n"
        "  \"cells\": [\n"
        "    {\"cell_type\": \"markdown\", \"id\": \"<unique_id>\", \"metadata\": {}, \"source\": [\"<Contenido de la sección>\"]},\n"
        "    {\"cell_type\": \"code\", \"execution_count\": null, \"id\": \"<unique_id>\", \"metadata\": {}, \"outputs\": [], \"source\": [\"<Código de ejemplo>\"]},\n"
        "    ...\n"
        "  ],\n"
        "  \"metadata\": {\n"
        "    \"kernelspec\": {\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"},\n"
        "    \"language_info\": {\"name\": \"python\", \"version\": \"3.x\"}\n"
        "  },\n"
        "  \"nbformat\": 4,\n"
        "  \"nbformat_minor\": 5\n"
        "}\n\n"
        "Genera únicamente este JSON y nada más."
    )
    user_prompt = text

    payload = {
        "model": LLM_MODEL_OPENAI,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": None,
        "n": 1,
        "temperature": 0.2,
        "stream": True
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY_OPENAI}",
        "Content-Type": "application/json"
    }
    if stream_placeholder:
        stream_placeholder.text("Procesando prompt, espere por favor...")
    response = requests.post(LLM_BASE_URL_OPENAI + "/v1/chat/completions", json=payload, headers=headers, stream=True)
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
                except Exception:
                    continue
    # Intentar extraer el bloque JSON delimitado por triple backticks, si existe
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
    return full_output, result

def join_ideas(unified_text, stream_placeholder=None):
    """
    Recibe un texto unificado (con la información consolidada de artículos afines)
    y llama a call_llm_for_sections para generar el JSON final del notebook.
    """
    result = call_llm_for_sections(unified_text, stream_placeholder=stream_placeholder)
    return result

# Prueba (opcional)
