import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  LinearProgress, 
  List, 
  ListItem, 
  ListItemText, 
  Divider, 
  Chip, 
  TextField,
  Button,
  IconButton,
  InputAdornment,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  ListItemAvatar,
  ListItemButton,
  Collapse,
  Alert,
  Tooltip,
  alpha,
  useTheme
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  OpenInNew as OpenInNewIcon,
  PictureAsPdf as PdfIcon,
  Article as ArticleIcon,
  LibraryBooks as LibraryIcon
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';

interface SearchResult {
  id: string;
  title: string;
  abstract: string;
  authors: Array<{ name: string }>;
  published?: string;
  categories?: string[];
  url: string;
  source: string;
  relevance?: number;
}

const SourceIcon = ({ source }: { source: string }) => {
  switch (source.toLowerCase()) {
    case 'arxiv':
      return <ArticleIcon />;
    case 'tds':
      return <LibraryIcon />;
    default:
      return <ArticleIcon />;
  }
};

const ResultItem = ({ result }: { result: SearchResult }) => {
  const [expanded, setExpanded] = React.useState(false);
  const theme = useTheme();

  return (
    <Paper 
      elevation={1} 
      sx={{ 
        mb: 2, 
        overflow: 'hidden',
        borderLeft: `3px solid ${theme.palette.primary.main}`
      }}
    >
      <ListItemButton onClick={() => setExpanded(!expanded)}>
        <ListItemAvatar>
          <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
            <SourceIcon source={result.source} />
          </Avatar>
        </ListItemAvatar>
        <ListItemText
          primary={
            <Typography 
              variant="subtitle1" 
              component="div"
              sx={{
                fontWeight: 500,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {result.title}
            </Typography>
          }
          secondary={
            <>
              <Typography
                component="span"
                variant="body2"
                color="text.primary"
                sx={{
                  display: 'block',
                  mt: 0.5,
                  mb: 0.5,
                  fontStyle: 'italic'
                }}
              >
                {result.authors?.map(a => a.name).join(', ')}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
                <Chip 
                  size="small" 
                  label={result.source} 
                  color="primary" 
                  variant="outlined"
                />
                {result.published && (
                  <Chip 
                    size="small" 
                    label={new Date(result.published).toLocaleDateString()} 
                    variant="outlined"
                  />
                )}
              </Box>
            </>
          }
        />
        {expanded ? <ExpandMoreIcon /> : <ExpandMoreIcon />}
      </ListItemButton>
      
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ p: 2, pt: 0, bgcolor: theme.palette.background.default }}>
          <Typography variant="body2" paragraph>
            {result.abstract || 'No hay resumen disponible.'}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {result.categories?.map((cat, i) => (
              <Chip 
                key={i} 
                label={cat} 
                size="small" 
                variant="outlined"
              />
            ))}
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, gap: 1 }}>
            {result.url && (
              <Tooltip title="Ver en la fuente original">
                <IconButton 
                  size="small" 
                  component="a" 
                  href={result.url} 
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <OpenInNewIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {result.url?.includes('arxiv') && (
              <Tooltip title="Ver PDF">
                <IconButton 
                  size="small" 
                  component="a" 
                  href={result.url.replace('/abs/', '/pdf/') + '.pdf'} 
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <PdfIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};

export const SearchResults: React.FC = () => {
  const theme = useTheme();
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<Record<string, SearchResult[]>>({});
  const [status, setStatus] = useState<string>('');
  const [sources, setSources] = useState<string[]>([]);
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const { send, addMessageHandler, isConnected, error } = useWebSocket('ws://localhost:8100/ws/search');

  // Manejar mensajes del WebSocket
  useEffect(() => {
    if (!addMessageHandler) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        console.log('Mensaje recibido:', data);

        switch (data.type) {
          case 'processing_started':
            setStatus(`Buscando en Arxiv...`);
            setIsSearching(true);
            setResults({});
            setSources(['arxiv']);
            break;

          case 'update':
            if (data.status === 'started') {
              setStatus(`Buscando en ${data.source}...`);
            } else if (data.status === 'results' && data.results) {
              setResults(prev => ({
                ...prev,
                [data.source]: data.results
              }));
              setActiveSource(data.source);
            } else if (data.status === 'completed') {
              setStatus(`Búsqueda en ${data.source} completada: ${data.data?.count || 0} resultados`);
            }
            break;

          case 'search_completed':
            setIsSearching(false);
            setStatus(`Búsqueda completada. Total de resultados: ${data.total_results || 0}`);
            if (data.results) {
              setResults(prev => ({
                ...prev,
                ...data.results
              }));
            }
            break;

          case 'search_started':
            setIsSearching(true);
            setStatus(`Buscando: ${data.query}`);
            break;


          case 'error':
            setIsSearching(false);
            setStatus(`Error: ${data.error || 'Error desconocido'}`);
            console.error('Error del servidor:', data.error);
            break;

          default:
            console.log('Mensaje no manejado:', data);
        }
      } catch (e) {
        console.error('Error procesando mensaje:', e);
      }
    };

    // Registrar el manejador de mensajes
    const removeHandler = addMessageHandler(handleMessage);

    // Limpieza al desmontar
    return () => {
      removeHandler();
    };
  }, [addMessageHandler]);

  const handleSearch = () => {
    if (!query.trim()) return;
    
    setStatus('Iniciando búsqueda en Arxiv...');
    setIsSearching(true);
    setResults({});
    
    // Forzar solo búsqueda en Arxiv
    send({
      type: 'search',
      query: query,
      sources: ['arxiv'],  // Solo Arxiv
      timestamp: new Date().toISOString()
    });
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Fecha no disponible';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (e) {
      return dateString;
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Controles de búsqueda */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, position: 'sticky', top: 16, zIndex: 1, maxWidth: '800px', mx: 'auto', width: '100%' }}>
        <Typography variant="h5" gutterBottom>Buscador de Artículos Académicos</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Busca artículos académicos en Arxiv
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ej: machine learning, deep learning, transformers..."
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              disabled={isSearching}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: query && (
                  <InputAdornment position="end">
                    <IconButton 
                      size="small" 
                      onClick={() => setQuery('')}
                      edge="end"
                      disabled={isSearching}
                    >
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={isSearching || !isConnected || !query.trim()}
            startIcon={isSearching ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
            sx={{ 
              whiteSpace: 'nowrap',
              minWidth: '120px',
              height: '40px'
            }}
          >
            {isSearching ? 'Buscando...' : 'Buscar'}
          </Button>
        </Box>

        {status && (
          <Box sx={{ mt: 2, mb: 1 }}>
            <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {status}
          </Typography>
        </Box>
            {isSearching && <LinearProgress sx={{ height: 2 }} />}
          </Box>
        )}

        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              mt: 2,
              '& .MuiAlert-message': {
                width: '100%'
              }
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
              <span>Error: {error}</span>
              <Button 
                color="inherit" 
                size="small" 
                onClick={() => window.location.reload()}
              >
                Recargar
              </Button>
            </Box>
          </Alert>
        )}
      </Paper>

      {/* Resultados */}
      <Box sx={{ width: '100%' }}>
        {sources.length === 0 && !isSearching && (
          <Paper 
            elevation={0} 
            sx={{ 
              p: 4, 
              textAlign: 'center',
              bgcolor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
              border: `1px dashed ${theme.palette.divider}`,
              borderRadius: 2
            }}
          >
            <SearchIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No hay resultados para mostrar
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Realiza una búsqueda para ver los resultados
            </Typography>
          </Paper>
        )}

        {sources.map((source) => {
          const sourceResults = results[source] || [];
          
          // Forzar visualización de Arxiv
          if (source !== 'arxiv') return null;
          
          return (
            <Accordion 
              key={source}
              defaultExpanded
              elevation={2}
              sx={{
                mb: 2,
                '&:before': {
                  display: 'none',
                },
                borderRadius: 2,
                overflow: 'hidden',
                border: `1px solid ${theme.palette.divider}`,
                '&.Mui-expanded': {
                  margin: 0,
                  mb: 2,
                },
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                  },
                  '&.Mui-expanded': {
                    minHeight: 48,
                  },
                  '& .MuiAccordionSummary-content': {
                    alignItems: 'center',
                    '&.Mui-expanded': {
                      margin: '12px 0',
                    },
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <Avatar 
                    sx={{ 
                      width: 32, 
                      height: 32, 
                      mr: 2,
                      bgcolor: theme.palette.primary.main,
                      color: theme.palette.primary.contrastText
                    }}
                  >
                    <SourceIcon source={source} />
                  </Avatar>
                  <Typography sx={{ fontWeight: 600, flexGrow: 1 }}>
                    {source.charAt(0).toUpperCase() + source.slice(1)}
                  </Typography>
                  <Chip 
                    label={sourceResults.length} 
                    size="small" 
                    color="primary"
                    variant="outlined"
                    sx={{ 
                      mr: 1,
                      fontWeight: 500
                    }} 
                  />
                </Box>
              </AccordionSummary>
              
              <AccordionDetails sx={{ p: 0, bgcolor: 'background.paper' }}>
                {sourceResults.length > 0 ? (
                  <List sx={{ width: '100%', p: 0 }}>
                    {sourceResults.map((result, index) => (
                      <React.Fragment key={result.id || index}>
                        <ResultItem result={result} />
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      No se encontraron resultados en {source}
                    </Typography>
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          );
        })}
        
        {isSearching && Object.keys(results).length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress size={40} thickness={4} />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Buscando en las fuentes seleccionadas...
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default SearchResults;
