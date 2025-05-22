import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Chip, IconButton, Drawer as MuiDrawer } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import extractionService from '../services/extractionService';
import { useWebSocket } from '../hooks/useWebSocket';

export interface Article {
  id: string;
  title: string;
  abstract: string;
  authors: Array<{ name: string }>;
  published?: string;
  categories?: string[];
  url: string;
  source: string;
  relevance?: number;
  primary_category?: string;
  version?: string | null;
  doi?: string;
  pdf_url?: string;
  github_links?: string[];
  github_link?: string;
  github_status?: string;
  [key: string]: any;
}

interface Props {
  selectedArticles: Article[];
  setSelectedArticles: React.Dispatch<React.SetStateAction<Article[]>>;
  sidebarMode?: boolean;
  onExpandPanel?: () => void; // Nuevo: para expandir desde el botón externo
}

const drawerWidth = 340;

// Utilidad para mostrar JSON bonito
function PrettyJSON({ data }: { data: any }) {
  return (
    <Box
      sx={{
        bgcolor: '#23272e',
        color: '#fff',
        borderRadius: 1,
        fontSize: 13,
        p: 2,
        overflowX: 'auto',
        fontFamily: 'monospace',
        mb: 1,
        maxHeight: 300,
      }}
      component="pre"
    >
      {JSON.stringify(data, null, 2)}
    </Box>
  );
}

const SelectedArticlesPanel = ({
  selectedArticles,
  setSelectedArticles,
  sidebarMode = false,
  onExpandPanel
}: Props) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, any>>({});
  // Mueve el estado de streaming y showExtraction FUERA del colapso para que no se pierda al colapsar
  const [streaming, setStreaming] = useState<Record<string, string>>({});
  const [showExtraction, setShowExtraction] = useState(false);
  const [stopRequested, setStopRequested] = useState(false);
  const [open, setOpen] = useState(true);
  const [wsId, setWsId] = useState<string | null>(null);
  const { ws, send, addMessageHandler, isConnected } = useWebSocket('ws://localhost:8100/ws/search');

  // Obtener y guardar el ws_id cuando el WebSocket lo envía
  useEffect(() => {
    if (!addMessageHandler) return;
    const handler = (event: MessageEvent) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        if (data.type === 'ws_id' && data.ws_id) {
          setWsId(data.ws_id);
          //console.log('[FRONTEND WS] ws_id recibido:', data.ws_id);
        }
        if (data.type === 'llm_stream' && data.ws_id && wsId && data.ws_id === wsId) {
          let artId: string = '';
          if (typeof data.article_id === 'string') {
            artId = data.article_id;
          } else if (selectedArticles.length === 1) {
            artId = selectedArticles[0].id;
          } else {
            artId = 'default';
          }
          //console.log('[FRONTEND WS] LLM_STREAM Chunk recibido:', data.content, 'para artId:', artId);
          setStreaming(prev => ({
            ...prev,
            [String(artId)]: data.full_output
          }));
        }
        if (data.type === 'llm_stream_done' && data.ws_id && wsId && data.ws_id === wsId) {
          //console.log('[FRONTEND WS] LLM_STREAM DONE recibido para ws_id:', data.ws_id);
        }
      } catch (err) {
        //console.error('[FRONTEND WS] Error procesando mensaje:', err, event.data);
      }
    };
    const remove = addMessageHandler(handler);
    return () => remove();
  }, [addMessageHandler, wsId, selectedArticles]);

  // Ref para el box de streaming (por artículo)
  const streamingRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Scroll automático al final cuando cambia el streaming
  useEffect(() => {
    Object.entries(streaming).forEach(([artId, _]) => {
      const ref = streamingRefs.current[artId];
      if (ref) {
        ref.scrollTop = ref.scrollHeight;
      }
    });
  }, [streaming]);

  // Nuevo: guardar el JSON parseado del streaming final para cada artículo
  const [parsedJson, setParsedJson] = useState<Record<string, any>>({});

  // Cuando termina el streaming (llm_stream_done), intenta parsear el JSON del streaming y lo guarda
  useEffect(() => {
    if (!addMessageHandler) return;
    const handler = (event: MessageEvent) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        if (data.type === 'llm_stream_done' && data.ws_id && wsId && data.ws_id === wsId) {
          // Buscar el artId igual que en el streaming
          let artId: string = '';
          if (typeof data.article_id === 'string') {
            artId = data.article_id;
          } else if (selectedArticles.length === 1) {
            artId = selectedArticles[0].id;
          } else {
            artId = 'default';
          }
          const streamText = streaming[artId];
          if (streamText) {
            // Intenta extraer el JSON del texto del streaming
            let jsonStr = '';
            let parsed: Record<string, any> | null = null;
            try {
              const match = streamText.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
              if (match) {
                jsonStr = match[1];
              } else {
                const start = streamText.indexOf('{');
                const end = streamText.lastIndexOf('}');
                if (start !== -1 && end !== -1 && end > start) {
                  jsonStr = streamText.slice(start, end + 1);
                }
              }
              if (jsonStr) {
                parsed = JSON.parse(jsonStr);
              }
            } catch (e) {
              parsed = null;
            }
            if (parsed) {
              setParsedJson(prev => ({
                ...prev,
                [artId]: parsed
              }));
            }
          }
        }
      } catch (err) {
        // Silenciar errores de parseo
      }
    };
    const remove = addMessageHandler(handler);
    return () => remove();
  }, [addMessageHandler, wsId, streaming, selectedArticles]);

  // Eliminar artículo de la selección (sin colapsar el panel)
  const handleRemoveArticle = (id: string) => {
    setSelectedArticles(prev => prev.filter(a => a.id !== id));
  };

  // Si el panel está minimizado y está en modo sidebar, muestra un botón flotante para restaurar
  if (!open && sidebarMode) {
    // El panel está colapsado, pero NO reseteamos el estado de streaming ni resultados
    return null;
  }

  // Panel compacto para el sidebar
  if (sidebarMode) {
    return open ? (
      <Box sx={{ p: 1, bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, justifyContent: 'center' }}>
          <Typography
            variant="subtitle1"
            sx={{ flex: 1, fontWeight: 600, textAlign: 'center' }}
          >
            Seleccionados ({selectedArticles.length})
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 1 }}>
          {selectedArticles.map((art, idx) => (
            <Chip
              key={art.id}
              label={`${idx + 1}. ${art.title}`}
              onDelete={() => handleRemoveArticle(art.id)}
              sx={{ maxWidth: 260, mb: 0.5 }}
            />
          ))}
        </Box>
        <Button
          variant="contained"
          onClick={async () => {
            setLoading(true);
            setStopRequested(false);
            setOpen(true);
            setStreaming({});
            setResults({});
            setShowExtraction(true);
            for (const art of selectedArticles) {
              if (stopRequested) break;
              try {
                const formData = new FormData();
                formData.append('pdf_url', art.pdf_url || '');
                if (wsId) formData.append('ws_id', wsId);
                await fetch('http://localhost:8100/extract-ideas', {
                  method: 'POST',
                  body: formData,
                });
                // El resultado final se mostrará cuando llegue por WebSocket (streaming)
              } catch (e) {
                setResults(prev => ({
                  ...prev,
                  [art.id]: { error: 'Error de red al extraer ideas.' }
                }));
              }
            }
            setLoading(false);
          }}
          disabled={loading || !selectedArticles.length || !wsId}
          startIcon={loading ? <CircularProgress size={18} /> : null}
          fullWidth
          sx={{ mb: 1 }}
        >
          Extraer Ideas y Conceptos
        </Button>
        {/* Mostrar logs y resultados SOLO si se hizo extracción */}
        {showExtraction && selectedArticles.map((art) => (
          <Accordion key={art.id} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                {art.title}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {/* Streaming completo */}
              {streaming[art.id] && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                    Streaming del modelo:
                  </Typography>
                  <Box
                    ref={el => { streamingRefs.current[art.id] = el as HTMLDivElement | null; }}
                    sx={{
                      bgcolor: '#181c20',
                      color: '#90caf9',
                      borderRadius: 1,
                      fontSize: 13,
                      p: 2,
                      overflowX: 'hidden',
                      overflowY: 'auto',
                      fontFamily: 'monospace',
                      mb: 1,
                      maxHeight: 200,
                      width: '100%',
                      wordBreak: 'break-word',
                      whiteSpace: 'pre-wrap',
                      transition: 'background 0.2s',
                    }}
                    component="pre"
                  >
                    {streaming[art.id]}
                  </Box>
                </Box>
              )}
              {/* Resultado final JSON bonito (del backend o del streaming parseado) */}
              {results[art.id]?.error ? (
                <Typography color="error">{results[art.id].error}</Typography>
              ) : parsedJson[art.id] ? (
                <>
                  <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                    Resumen estructurado:
                  </Typography>
                  <PrettyJSON data={parsedJson[art.id]} />
                </>
              ) : (
                results[art.id] && (
                  <>
                    <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                      Resumen estructurado:
                    </Typography>
                    <PrettyJSON data={results[art.id]} />
                  </>
                )
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    ) : null;
  }

  // Drawer lateral izquierdo para artículos seleccionados
  return (
    <MuiDrawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          p: 2,
          bgcolor: 'background.paper',
          zIndex: 1300
        }
      }}
      PaperProps={{ sx: { p: 2 } }}
    >
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        {selectedArticles.map((art, idx) => (
          <Chip
            key={art.id}
            label={`${idx + 1}. ${art.title}`}
            onDelete={() => handleRemoveArticle(art.id)}
            sx={{ maxWidth: 300 }}
          />
        ))}
      </Box>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
        <Button
          variant="contained"
          onClick={async () => {
            setLoading(true);
            setStopRequested(false);
            setOpen(true);
            setStreaming({});
            setResults({});
            setShowExtraction(true);
            for (const art of selectedArticles) {
              if (stopRequested) break;
              try {
                const formData = new FormData();
                formData.append('pdf_url', art.pdf_url || '');
                if (wsId) formData.append('ws_id', wsId);
                await fetch('http://localhost:8100/extract-ideas', {
                  method: 'POST',
                  body: formData,
                });
                // El resultado final se mostrará cuando llegue por WebSocket (streaming)
              } catch (e) {
                setResults(prev => ({
                  ...prev,
                  [art.id]: { error: 'Error de red al extraer ideas.' }
                }));
              }
            }
            setLoading(false);
          }}
          disabled={loading || !selectedArticles.length || !wsId}
          startIcon={loading ? <CircularProgress size={18} /> : null}
        >
          Extraer Ideas y Conceptos
        </Button>
        <Button
          variant="outlined"
          color="error"
          onClick={() => setStopRequested(true)}
          disabled={!loading}
        >
          Parar extracción
        </Button>
      </Box>
      {/* Mostrar logs y resultados SOLO si se hizo extracción */}
      {showExtraction && selectedArticles.map((art) => (
        <Accordion key={art.id} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="subtitle1">
              {art.title}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {/* Streaming completo */}
            {streaming[art.id] && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                  Streaming del modelo:
                </Typography>
                <Box
                  ref={el => { streamingRefs.current[art.id] = el as HTMLDivElement | null; }}
                  sx={{
                    bgcolor: '#181c20',
                    color: '#90caf9',
                    borderRadius: 1,
                    fontSize: 13,
                    p: 2,
                    overflowX: 'hidden',
                    overflowY: 'auto',
                    fontFamily: 'monospace',
                    mb: 1,
                    maxHeight: 200,
                    width: '100%',
                    wordBreak: 'break-word',
                    whiteSpace: 'pre-wrap',
                    transition: 'background 0.2s',
                  }}
                  component="pre"
                >
                  {streaming[art.id]}
                </Box>
              </Box>
            )}
            {/* Resultado final JSON bonito (del backend o del streaming parseado) */}
            {results[art.id]?.error ? (
              <Typography color="error">{results[art.id].error}</Typography>
            ) : parsedJson[art.id] ? (
              <>
                <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                  Resumen estructurado:
                </Typography>
                <PrettyJSON data={parsedJson[art.id]} />
              </>
            ) : (
              results[art.id] && (
                <>
                  <Typography variant="caption" color="primary" sx={{ fontWeight: 600 }}>
                    Resumen estructurado:
                  </Typography>
                  <PrettyJSON data={results[art.id]} />
                </>
              )
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </MuiDrawer>
  );
};

export default SelectedArticlesPanel;
