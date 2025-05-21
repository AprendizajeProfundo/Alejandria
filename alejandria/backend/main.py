from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

@app.websocket("/ws/search")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para búsquedas en tiempo real"""
    connection_id = str(uuid.uuid4())[:8]
    
    # Aceptar la conexión
    await websocket.accept()
    logger.info(f"[WS:{connection_id}] Conexión WebSocket aceptada")
    
    try:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
