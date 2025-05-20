import { useEffect, useRef, useState } from 'react';

interface WebSocketMessageEvent extends MessageEvent {
  data: string;
}

type MessageHandler = (event: MessageEvent) => void;

interface UseWebSocketReturn {
  ws: WebSocket | null;
  send: (data: any) => boolean;
  addMessageHandler: (handler: MessageHandler) => () => void;
  readyState: number;
  error: string | null;
  reconnect: () => void;
  isConnected: boolean;
}

export const useWebSocket = (url: string = 'ws://localhost:8100/ws/search', isTest: boolean = false): UseWebSocketReturn => {
  const wsRef = useRef<WebSocket | null>(null);
  const [readyState, setReadyState] = useState<WebSocket['readyState']>(WebSocket.CONNECTING);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const messageHandlers = useRef<Set<MessageHandler>>(new Set());
  const maxRetries = 10;
  const retryDelay = 2000; // 2 segundos
  const reconnectAttempts = useRef(0);

  const handleMessage = (event: MessageEvent) => {
    console.log('Raw WebSocket message:', event.data);
    try {
      const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
      console.log('Parsed WebSocket message:', data);
      
      // Notificar a todos los manejadores registrados
      messageHandlers.current.forEach(handler => {
        try {
          handler(event);
        } catch (handlerError) {
          console.error('Error in message handler:', handlerError);
        }
      });
      
      // Si estamos en el entorno de Electron, también enviar el mensaje a través de IPC
      if (window.electron) {
        window.electron.ipcRenderer.send('websocket-message', data);
      }
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
      setError('Error parsing message: ' + e);
    }
  };

  const initializeWebSocket = () => {
    if (wsRef.current) {
      console.log('Cerrando conexión WebSocket existente...');
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
    }

    const testUrl = isTest ? 'ws://localhost:8100/ws/test' : url;
    console.log(`Inicializando WebSocket: ${testUrl}`);
    
    try {
      const ws = new WebSocket(testUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connection opened');
        setReadyState(WebSocket.OPEN);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        setReadyState(WebSocket.CLOSED);
        
        // Código de error 1000 es normal, no necesitamos reintentar
        if (event.code === 1000) {
          console.log('Conexión cerrada normalmente');
          return;
        }

        // Para otros códigos de error, intentamos reintentar
        if (reconnectAttempts.current < maxRetries) {
          reconnectAttempts.current += 1;
          const delay = retryDelay * Math.pow(1.5, reconnectAttempts.current - 1);
          console.log(`Reintentando conexión en ${delay}ms (intento ${reconnectAttempts.current}/${maxRetries})...`);
          
          setTimeout(() => {
            if (wsRef.current?.readyState === WebSocket.CLOSED) {
              initializeWebSocket();
            }
          }, delay);
        } else {
          const errorMsg = `No se pudo conectar después de ${maxRetries} intentos`;
          console.error(errorMsg);
          setError(errorMsg);
        }
      };

      ws.onerror = (event) => {
        const errorMessage = `WebSocket error: ${event.type}`;
        console.error('❌ WebSocket error:', event);
        setError(errorMessage);
      };

      ws.onmessage = handleMessage;
      
    } catch (e) {
      console.error('Error al crear WebSocket:', e);
      setError(`Error al conectar: ${e}`);
    }
  };

  useEffect(() => {
    initializeWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url]);

  const addMessageHandler = (handler: MessageHandler) => {
    messageHandlers.current.add(handler);
    return () => messageHandlers.current.delete(handler);
  };

  const send = (data: any) => {
    if (!wsRef.current) {
      const errorMsg = 'WebSocket no está inicializado';
      console.error(errorMsg);
      setError(errorMsg);
      return false;
    }

    if (wsRef.current.readyState !== WebSocket.OPEN) {
      const errorMsg = `WebSocket no está conectado (estado: ${wsRef.current.readyState})`;
      console.error(errorMsg);
      setError(errorMsg);
      
      // Intentar reconectar si es posible
      if (reconnectAttempts.current < maxRetries) {
        console.log('Intentando reconectar...');
        initializeWebSocket();
      }
      
      return false;
    }

    try {
      const message = JSON.stringify(data);
      console.log('Enviando mensaje WebSocket:', message);
      wsRef.current.send(message);
      return true;
    } catch (e) {
      const errorMsg = `Error enviando mensaje: ${e}`;
      console.error(errorMsg);
      setError(errorMsg);
      return false;
    }
  };

  return {
    ws: wsRef.current,
    send,
    readyState,
    error,
    addMessageHandler,
    reconnect: initializeWebSocket,
    isConnected: readyState === WebSocket.OPEN
  };
};
