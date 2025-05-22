import React, { useState, useEffect } from 'react';
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

const SelectedArticlesPanel = ({
  selectedArticles,
  setSelectedArticles,
  sidebarMode = false,
  onExpandPanel
}: Props) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, any>>({});
  const [streaming, setStreaming] = useState<Record<string, string>>({});
  const [stopRequested, setStopRequested] = useState(false);
  const [open, setOpen] = useState(true);
  const wsId = React.useRef<string>(Math.random().toString(36).slice(2, 10)).current;

  const { send, addMessageHandler } = useWebSocket('ws://localhost:8100/ws/search');

  // Sincronizar cierre del panel con la X (minimizar, no limpiar selección)
  const handleMinimize = () => setOpen(false);

  // Si el usuario hace click en el botón de extraer, colapsar el panel
  const handleExtract = async () => {
    setLoading(true);
    setStopRequested(false);
    setOpen(false);
    const newResults: Record<string, any> = {};
    for (const art of selectedArticles) {
      if (stopRequested) break;
      try {
        const formData = new FormData();
        formData.append('pdf_url', art.pdf_url || '');
        formData.append('ws_id', wsId);
        const res = await fetch('http://localhost:8100/extract-ideas', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          newResults[art.id] = { error: 'Error al extraer ideas del backend.' };
        } else {
          newResults[art.id] = await res.json();
        }
      } catch (e) {
        newResults[art.id] = { error: 'Error de red al extraer ideas.' };
      }
    }
    setResults(newResults);
    setLoading(false);
  };

  // Mostrar logs y streaming en tiempo real
  useEffect(() => {
    if (!addMessageHandler) return;
    const handler = (event: MessageEvent) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        if (data.type === 'llm_stream' && data.ws_id === wsId && data.full_output && data.content) {
          // eslint-disable-next-line no-console
          console.log('[LLM_STREAM] Chunk recibido:', data.content);
          console.log('[LLM_STREAM] Acumulado:', data.full_output);
          setStreaming(prev => ({
            ...prev,
            [data.article_id || data.ws_id]: data.full_output
          }));
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[LLM_STREAM] Error procesando mensaje:', err, event.data);
      }
    };
    const remove = addMessageHandler(handler);
    return () => remove();
  }, [addMessageHandler, wsId]);

  // Si el panel está minimizado y está en modo sidebar, muestra un botón flotante para restaurar
  if (!open && sidebarMode) {
    // Elimina el botón con ChevronLeftIcon (hacia la izquierda)
    return null;
  }

  // Panel compacto para el sidebar
  if (sidebarMode) {
    return open ? (
      <Box sx={{ p: 1, bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ flex: 1, fontWeight: 600 }}>
            Seleccionados ({selectedArticles.length})
          </Typography>
          <IconButton
            size="small"
            onClick={handleMinimize}
            sx={{ ml: 1 }}
            title="Minimizar panel"
          >
        
          </IconButton>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 1 }}>
          {selectedArticles.map((art, idx) => (
            <Chip
              key={art.id}
              label={`${idx + 1}. ${art.title}`}
              onDelete={handleMinimize}
              sx={{ maxWidth: 260, mb: 0.5 }}
            />
          ))}
        </Box>
        <Button
          variant="contained"
          onClick={handleExtract}
          disabled={loading || !selectedArticles.length}
          startIcon={loading ? <CircularProgress size={18} /> : null}
          fullWidth
          sx={{ mb: 1 }}
        >
          Extraer Ideas y Conceptos
        </Button>
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
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ flex: 1 }}>Artículos seleccionados ({selectedArticles.length})</Typography>
        <IconButton
          size="small"
          onClick={handleMinimize}
          sx={{ ml: 2 }}
          title="Minimizar panel"
        >
          <ChevronLeftIcon />
        </IconButton>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        {selectedArticles.map((art, idx) => (
          <Chip
            key={art.id}
            label={`${idx + 1}. ${art.title}`}
            // No elimina, solo minimiza
            onDelete={handleMinimize}
            sx={{ maxWidth: 300 }}
          />
        ))}
      </Box>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
        <Button
          variant="contained"
          onClick={handleExtract}
          disabled={loading || !selectedArticles.length}
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
      <Box>
        {selectedArticles.map((art) => (
          <Accordion key={art.id} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                {art.title}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {streaming[art.id] && (
                <Typography sx={{ fontFamily: 'monospace', color: 'primary.main', mb: 2 }}>
                  {streaming[art.id]}
                </Typography>
              )}
              {results[art.id]?.error ? (
                <Typography color="error">{results[art.id].error}</Typography>
              ) : (
                results[art.id] && (
                  <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {JSON.stringify(results[art.id], null, 2)}
                  </pre>
                )
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </MuiDrawer>
  );
};

export default SelectedArticlesPanel;
