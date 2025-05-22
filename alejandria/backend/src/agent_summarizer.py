# agent_summarizer.py

import re
import requests
import json
import PyPDF2
import asyncio
from .config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

def extract_full_text_from_pdf(pdf_path):
    """
    Extrae todo el texto del PDF.
    """
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        # Manejo de error para archivos PDF corruptos o ilegibles
        text += f"\n[ERROR] No se pudo extraer el texto del PDF: {e}\n"
    return text[:200]  # <-- Devuelve el texto completo, no solo los primeros 200 caracteres

def call_llm_for_summary(text, stream_placeholder=None, ws=None, ws_id=None):
    """
    Llama al LLM para extraer un resumen pedagógico del artículo.
    Si ws (WebSocket) es provisto, envía el progreso en tiempo real.
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

    if stream_placeholder:
        stream_placeholder.text("Procesando Prompt de Extracción. Espere por favor...")

    response = requests.post(LLM_BASE_URL + "/chat/completions", json=payload, headers=headers, stream=True)
    if response.status_code != 200:
        raise Exception(f"Error en la llamada al LLM: {response.status_code} {response.text}")

    full_output = ""
    # Detectar si estamos en un thread sin event loop y crear uno temporal para enviar por WS
    loop = None
    if ws:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No hay event loop en este thread, crear uno temporal
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8").strip()
            #print(f"[BACKEND LLM_STREAM] Recibido: {decoded_line[:120]}{'...' if len(decoded_line) > 120 else ''}")
            if decoded_line.startswith("data:"):
                data_line = decoded_line[5:].strip()
                if data_line == "[DONE]":
                    #print("[BACKEND LLM_STREAM] Fin del stream ([DONE])")
                    if ws:
                        msg = {
                            "type": "llm_stream_done",
                            "ws_id": ws_id,
                        }
                        try:
                            if loop and loop.is_running():
                                asyncio.run_coroutine_threadsafe(ws.send_json(msg), loop)
                            else:
                                loop.run_until_complete(ws.send_json(msg))
                        except Exception as e:
                            #print(f"[BACKEND LLM_STREAM] Error enviando DONE por WS: {e}")
                            pass
                    break
                try:
                    data_json = json.loads(data_line)
                    if "choices" in data_json:
                        for choice in data_json["choices"]:
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                full_output += content
                                #print(f"[BACKEND LLM_STREAM] Chunk: {content[:80]}")
                                if stream_placeholder:
                                    stream_placeholder.text(full_output)
                                if ws:
                                    msg = {
                                        "type": "llm_stream",
                                        "ws_id": ws_id,
                                        "content": content,
                                        "full_output": full_output
                                    }
                                    try:
                                        if loop and loop.is_running():
                                            asyncio.run_coroutine_threadsafe(ws.send_json(msg), loop)
                                        else:
                                            loop.run_until_complete(ws.send_json(msg))
                                        #print(f"[BACKEND LLM_STREAM] Enviado chunk por WS (ws_id={ws_id})")
                                    except Exception as e:
                                        #print(f"[BACKEND LLM_STREAM] Error enviando chunk por WS: {e}")
                                        pass
                except Exception as e:
                    #print(f"[BACKEND LLM_STREAM] Error procesando chunk: {e}")
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
    return full_output, result

def summarize_pdf(pdf_path, stream_placeholder=None, ws=None, ws_id=None):
    """
    Extrae el texto completo del PDF y llama al LLM para obtener el resumen pedagógico.
    Si ws está presente, hace streaming en tiempo real.
    """
    text = extract_full_text_from_pdf(pdf_path)
    if not text or "[ERROR]" in text:
        return "", {
            "main_ideas": [],
            "methods": [],
            "comparisons": [],
            "algorithms": [],
            "other": [],
            "error": "No se pudo extraer texto del PDF."
        }
    summary = call_llm_for_summary(text, stream_placeholder=stream_placeholder, ws=ws, ws_id=ws_id)
    return summary

# Prueba (opcional)
if __name__ == "__main__":
    test_pdf = "papers/input/example.pdf"
    res = summarize_pdf(test_pdf)
    print(json.dumps(res, indent=2))
