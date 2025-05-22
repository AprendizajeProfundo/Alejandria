from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Any
import json
import uuid
import asyncio
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar componentes de la aplicación
from src.services.search_service import SearchService
from src.agent_summarizer import summarize_pdf

app = FastAPI(title="Alejandria API")

# Configurar CORS más explícito
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001"  # Nuevo puerto del frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Inicializar el servicio de búsqueda
search_service = SearchService()

def is_websocket_connected(ws: WebSocket) -> bool:
    """Verifica si el WebSocket sigue conectado"""
    try:
        return ws.client_state.value == 1  # WebSocketState.CONNECTED
    except Exception:
        return False

async def safe_send_json(ws: WebSocket, data: Dict, connection_id: str) -> bool:
    """Envía un mensaje JSON de forma segura"""
    try:
        await ws.send_json(data)
        return True
    except Exception as e:
        logger.error(f"[WS:{connection_id}] Error enviando mensaje: {e}")
        return False

# --- Registro global de websockets activos por ws_id ---
import threading
active_websockets = {}
active_websockets_lock = threading.Lock()

@app.websocket("/ws/search")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para búsquedas en tiempo real y streaming de extracción."""
    connection_id = str(uuid.uuid4())[:8]
    ws_id = None

    # Aceptar la conexión
    await websocket.accept()
    logger.info(f"[WS:{connection_id}] Conexión WebSocket aceptada")

    try:
        # Registrar el websocket con un ws_id único para extracción
        ws_id = str(uuid.uuid4())
        with active_websockets_lock:
            active_websockets[ws_id] = websocket

        # Enviar el ws_id al frontend para que lo use en /extract-ideas
        await safe_send_json(websocket, {
            "type": "ws_id",
            "ws_id": ws_id,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)

        # Mantener la conexión abierta y procesar múltiples búsquedas
        while is_websocket_connected(websocket):
            try:
                logger.info(f"[WS:{connection_id}] Esperando mensaje del cliente...")
                data = await websocket.receive_text()
                logger.info(f"[WS:{connection_id}] Mensaje recibido: {data[:200]}...")
                ack_message = {
                    "type": "acknowledge",
                    "message": "Mensaje recibido correctamente",
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.info(f"[WS:{connection_id}] Enviando ACK")
                await safe_send_json(websocket, ack_message, connection_id)
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "search":
                    try:
                        query = message.get("query", "").strip()
                        sources = ["arxiv"]

                        # Extraer todos los parámetros relevantes del mensaje
                        max_results = message.get("max_results", 10)
                        sortby = message.get("sortby", "relevance")
                        type_query = message.get("type_query", "all")
                        start = message.get("start", 0)
                        sortorder = message.get("sortorder", "descending")

                        logger.info(f"[WS:{connection_id}] Parámetros recibidos del frontend: query={query}, max_results={max_results}, sortby={sortby}, type_query={type_query}, start={start}, sortorder={sortorder}")

                        if not query:
                            error_msg = "La consulta no puede estar vacía"
                            logger.error(f"[WS:{connection_id}] {error_msg}")
                            await safe_send_json(websocket, {
                                "type": "error",
                                "error": error_msg,
                                "timestamp": datetime.utcnow().isoformat()
                            }, connection_id)
                            continue

                        logger.info(f"[WS:{connection_id}] Iniciando búsqueda: '{query}' en Arxiv")
                        await safe_send_json(websocket, {
                            "type": "search_started",
                            "message": f"Buscando en Arxiv: {query}",
                            "timestamp": datetime.utcnow().isoformat()
                        }, connection_id)
                        await safe_send_json(websocket, {
                            "type": "processing_started",
                            "message": "Procesando Arxiv...",
                            "sources": sources,
                            "timestamp": datetime.utcnow().isoformat()
                        }, connection_id)

                        # Pasa los parámetros al search_service
                        search_results = await search_service.search(
                            query=query,
                            sources=sources,
                            websocket=websocket,
                            max_results=max_results,
                            sortby=sortby,
                            type_query=type_query,
                            start=start,
                            sortorder=sortorder
                        )

                        if search_results.get("status") == "error":
                            error_msg = search_results.get("error", "Error desconocido en la búsqueda")
                            logger.error(f"[WS:{connection_id}] {error_msg}")
                            continue

                        total_results = sum(len(r) for r in search_results.get('results', {}).values())
                        logger.info(f"[WS:{connection_id}] Búsqueda completada con {total_results} resultados")
                        await safe_send_json(websocket, {
                            "type": "search_completed",
                            "query": query,
                            "total_results": total_results,
                            "sources_searched": len(sources),
                            "results": search_results.get('results', {}),
                            "timestamp": datetime.utcnow().isoformat()
                        }, connection_id)

                    except Exception as e:
                        error_msg = f"Error inesperado: {str(e)}"
                        logger.error(f"[WS:{connection_id}] {error_msg}", exc_info=True)
                        await safe_send_json(websocket, {
                            "type": "error",
                            "error": error_msg,
                            "timestamp": datetime.utcnow().isoformat()
                        }, connection_id)
                
            except json.JSONDecodeError as e:
                error_msg = f"Error decodificando JSON: {str(e)}"
                logger.error(error_msg)
                await safe_send_json(websocket, {
                    "type": "error",
                    "error": "Formato de mensaje inválido. Se espera un JSON válido.",
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }, connection_id)
                
            except WebSocketDisconnect as e:
                logger.info(f"[WS:{connection_id}] Cliente desconectado: {e}")
                break
                
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await safe_send_json(websocket, {
                    "type": "error",
                    "error": "Error interno del servidor",
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }, connection_id)
                
    except Exception as e:
        error_msg = f"Error en WebSocket: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
    finally:
        logger.info(f"[WS:{connection_id}] Cerrando conexión WebSocket...")
        try:
            if ws_id:
                with active_websockets_lock:
                    active_websockets.pop(ws_id, None)
            await websocket.close()
            logger.info(f"[WS:{connection_id}] Conexión WebSocket cerrada")
        except Exception as e:
            logger.error(f"[WS:{connection_id}] Error cerrando WebSocket: {str(e)}")
        print("Conexión WebSocket cerrada")

@app.get("/")
async def root():
    return {"message": "Alejandria API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-05-19T22:47:45+00:00"}

@app.post("/extract-ideas")
async def extract_ideas(request: Request):
    """
    Extrae ideas/conceptos de un PDF usando el agente de resumen.
    Si ws_id es proporcionado, hace streaming por WebSocket y NO espera el resultado final.
    Si no hay ws_id, hace streaming HTTP (chunked).
    """
    import tempfile
    import requests
    import os

    # Leer el form-data manualmente para soportar streaming
    form = await request.form()
    pdf_url = form.get("pdf_url")
    ws_id = form.get("ws_id")

    websocket = None
    if ws_id:
        with active_websockets_lock:
            websocket = active_websockets.get(ws_id)

    try:
        print(f"[extract-ideas] Intentando descargar PDF desde: {pdf_url}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            r = requests.get(pdf_url, timeout=30)
            print(f"[extract-ideas] Código de estado de la descarga: {r.status_code}")
            if r.status_code != 200:
                print(f"[extract-ideas] Error descargando PDF: {r.status_code} - {r.text[:200]}")
                return JSONResponse(content={"error": f"Error descargando PDF: {r.status_code}"}, status_code=400)
            tmp.write(r.content)
            tmp_path = tmp.name
            print(f"[extract-ideas] PDF guardado temporalmente en: {tmp_path}")

        # Si hay WebSocket, lanzar el procesamiento en background y responder inmediatamente
        if websocket:
            import threading
            def run_summarizer():
                try:
                    print(f"[extract-ideas] (thread) Llamando a summarize_pdf para: {tmp_path} (WebSocket streaming)")
                    from src.agent_summarizer import summarize_pdf
                    _, result = summarize_pdf(tmp_path, ws=websocket, ws_id=ws_id)
                    print(f"[extract-ideas] (thread) summarize_pdf terminado para: {tmp_path}")
                except Exception as e:
                    print(f"[extract-ideas] (thread) Error en summarize_pdf: {str(e)}")
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            threading.Thread(target=run_summarizer, daemon=True).start()
            # Responder inmediatamente, el frontend recibirá el streaming por WebSocket
            return JSONResponse(content={"status": "processing", "ws_id": ws_id})

        # Si NO hay WebSocket, hacer streaming HTTP (chunked)
        else:
            def stream_generator():
                try:
                    from src.agent_summarizer import call_llm_for_summary, extract_full_text_from_pdf
                    text = extract_full_text_from_pdf(tmp_path)
                    if not text or "[ERROR]" in text:
                        yield json.dumps({"error": "No se pudo extraer texto del PDF."}) + "\n"
                        return
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
                        "model": "deepseek-r1-distill-qwen-14b",
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
                        "Authorization": f"Bearer lm-studio",
                        "Content-Type": "application/json"
                    }
                    import requests
                    response = requests.post("http://localhost:1234/v1/chat/completions", json=payload, headers=headers, stream=True)
                    if response.status_code != 200:
                        yield json.dumps({"error": f"Error en la llamada al LLM: {response.status_code} {response.text}"}) + "\n"
                        return
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
                                                yield content
                                except Exception:
                                    pass
                    # Al final, intentar extraer el JSON y devolverlo como bloque final
                    import re
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
                    except Exception:
                        result = {}
                    yield "\n---JSON_RESULT---\n" + json.dumps(result)
                finally:
                    os.unlink(tmp_path)
            return StreamingResponse(stream_generator(), media_type="text/plain")
    except Exception as e:
        print(f"[extract-ideas] Error general: {str(e)}")
        return JSONResponse(content={"error": f"Error general: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
