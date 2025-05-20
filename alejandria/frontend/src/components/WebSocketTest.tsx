import React, { useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Button, Box, Typography, Paper } from '@mui/material';

export const WebSocketTest: React.FC = () => {
  const { 
    ws, 
    send, 
    readyState, 
    error, 
    reconnect, 
    isConnected 
  } = useWebSocket('ws://localhost:8100/ws/test', true);

  // Manejar mensajes del WebSocket
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      console.log('Mensaje de prueba recibido:', event.data);
    };

    if (ws) {
      ws.addEventListener('message', handleMessage);
      return () => {
        ws.removeEventListener('message', handleMessage);
      };
    }
  }, [ws]);

  const handleTestConnection = () => {
    if (isConnected) {
      send({ type: 'ping', timestamp: Date.now() });
    } else {
      reconnect();
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3, backgroundColor: '#f5f5f5' }}>
      <Typography variant="h6" gutterBottom>
        Prueba de Conexión WebSocket
      </Typography>
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="body1" gutterBottom>
          Estado: 
          <Typography 
            component="span" 
            color={isConnected ? 'success.main' : 'error.main'}
            sx={{ fontWeight: 'bold', ml: 1 }}
          >
            {isConnected ? 'Conectado' : 'Desconectado'}
          </Typography>
        </Typography>
        
        {error && (
          <Typography color="error" variant="body2" sx={{ mt: 1, p: 1, backgroundColor: '#ffebee', borderRadius: 1 }}>
            Error: {error}
          </Typography>
        )}
      
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            color={isConnected ? 'primary' : 'secondary'}
            onClick={handleTestConnection}
            disabled={!ws}
          >
            {isConnected ? 'Enviar Ping' : 'Conectar'}
          </Button>
          
          {isConnected && (
            <Button
              variant="outlined"
              color="error"
              onClick={() => ws?.close()}
            >
              Cerrar Conexión
            </Button>
          )}
        </Box>
      </Box>
    </Paper>
  );
};
