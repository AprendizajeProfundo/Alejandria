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
  ListItemIcon,
  Alert,
  Tooltip,
  alpha,
  useTheme,
  Checkbox,
  Link as MuiLink,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Box as MuiBox
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
import GitHubIcon from '@mui/icons-material/GitHub';
import CancelIcon from '@mui/icons-material/Cancel';
import DescriptionIcon from '@mui/icons-material/Description';

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
  primary_category?: string;
  version?: string | null;
  doi?: string;
  pdf_url?: string;
  github_links?: string[];
  github_link?: string;
  github_status?: string;
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

// Resalta los términos de búsqueda en el resumen
function highlightText(text: string, query: string) {
  if (!query) return text;
  const words = query.split(/\s+/).filter(Boolean);
  if (!words.length) return text;
  const pattern = new RegExp(`(${words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  return text.replace(pattern, match => `<mark style="background-color: #ffe082; color: #222;">${match}</mark>`);
}

export const SearchResults: React.FC = () => {
  const theme = useTheme();
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<Record<string, SearchResult[]>>({});
  const [status, setStatus] = useState<string>('');
  const [sources, setSources] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  // NUEVO: controles para tipo de búsqueda y número de resultados
  const [maxResults, setMaxResults] = useState(10);
  const [sortBy, setSortBy] = useState('relevance');
  const [typeQuery, setTypeQuery] = useState('all');

  const { send, addMessageHandler, isConnected, error } = useWebSocket('ws://localhost:8100/ws/search');

  useEffect(() => {
    if (!addMessageHandler) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
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
            break;
          default:
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('Error procesando mensaje:', e);
      }
    };

    const removeHandler = addMessageHandler(handleMessage);
    return () => {
      removeHandler();
    };
  }, [addMessageHandler]);

  const handleSearch = () => {
    if (!query.trim()) return;
    // LOG: Mostrar en consola lo que selecciona el usuario antes de enviar
    console.log("[Search] Parámetros enviados:", {
      query,
      max_results: maxResults,
      sortby: sortBy,
      type_query: typeQuery,
      start: 0,
      sortorder: 'descending'
    });
    setStatus('Iniciando búsqueda en Arxiv...');
    setIsSearching(true);
    setResults({});
    send({
      type: 'search',
      query: query,
      sources: ['arxiv'],
      max_results: maxResults,
      sortby: sortBy,
      type_query: typeQuery,
      start: 0,
      sortorder: 'descending',
      timestamp: new Date().toISOString()
    });
  };

  const handleToggle = (id: string) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  // También puedes agregar logs en los handlers de los filtros para ver cambios en tiempo real:
  useEffect(() => {
    console.log("[Filtro] sortBy:", sortBy, "| maxResults:", maxResults, "| typeQuery:", typeQuery);
  }, [sortBy, maxResults, typeQuery]);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Controles de búsqueda */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, maxWidth: '800px', mx: 'auto', width: '100%' }}>
        <Typography variant="h5" gutterBottom>Buscador de Artículos Académicos</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Busca artículos académicos en Arxiv
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
          <Box sx={{ flexGrow: 1, minWidth: 220 }}>
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
        {/* Filtros debajo del campo de búsqueda, más espaciados y slider más grande */}
        <MuiBox sx={{ display: 'flex', gap: 4, alignItems: 'center', mt: 4, mb: 2, flexWrap: 'wrap', justifyContent: 'space-between' }}>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel id="sortby-label">Ordenar por</InputLabel>
            <Select
              labelId="sortby-label"
              value={sortBy}
              label="Ordenar por"
              onChange={e => setSortBy(e.target.value)}
              disabled={isSearching}
            >
              <MenuItem value="relevance">Relevancia</MenuItem>
              <MenuItem value="lastUpdatedDate">Última actualización</MenuItem>
              <MenuItem value="submittedDate">Fecha de envío</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel id="type-query-label">Tipo</InputLabel>
            <Select
              labelId="type-query-label"
              value={typeQuery}
              label="Tipo"
              onChange={e => setTypeQuery(e.target.value)}
              disabled={isSearching}
            >
              <MenuItem value="all">Todo</MenuItem>
              <MenuItem value="title">Título</MenuItem>
              <MenuItem value="author">Autor</MenuItem>
            </Select>
          </FormControl>
          <Box sx={{ flexGrow: 1, minWidth: 320, maxWidth: 400 }}>
            <Typography id="slider-max-results" gutterBottom variant="caption" color="text.secondary">
              N° resultados: {maxResults}
            </Typography>
            <Slider
              value={maxResults}
              onChange={(_, v) => setMaxResults(v as number)}
              min={1}
              max={100}
              step={1}
              valueLabelDisplay="auto"
              disabled={isSearching}
              aria-labelledby="slider-max-results"
              sx={{ mt: -1 }}
            />
          </Box>
        </MuiBox>
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

      {/* Resultados en acordeón por fuente */}
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
                    {sourceResults.map((article) => (
                      <Accordion
                        key={article.id}
                        sx={{
                          mb: 1,
                          borderRadius: 2,
                          boxShadow: 1,
                          bgcolor: selected.includes(article.id) ? 'primary.lighter' : 'background.paper'
                        }}
                      >
                        <AccordionSummary
                          expandIcon={<ExpandMoreIcon />}
                          sx={{
                            minHeight: 48,
                            '& .MuiAccordionSummary-content': {
                              alignItems: 'center'
                            }
                          }}
                        >
                          <Checkbox
                            edge="start"
                            checked={selected.includes(article.id)}
                            onChange={() => handleToggle(article.id)}
                            color="primary"
                            sx={{ mr: 1 }}
                          />
                          <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>
                            {article.title}
                          </Typography>
                          {/* Iconos cerca del título */}
                          {/* GitHub solo si hay link */}
                          {article.github_link && (
                            <Tooltip title={`GitHub: ${article.github_link}`}>
                              <IconButton
                                size="small"
                                component="a"
                                href={article.github_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{ ml: 1 }}
                                onClick={e => e.stopPropagation()} // No expandir el acordeón al hacer click
                              >
                                <GitHubIcon
                                  color={
                                    article.github_status === 'OK'
                                      ? 'success'
                                      : article.github_status === 'Broken'
                                      ? 'error'
                                      : 'disabled'
                                  }
                                />
                              </IconButton>
                            </Tooltip>
                          )}
                          {/* Fecha de publicación */}
                          {article.published && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                              {new Date(article.published).toLocaleDateString()}
                            </Typography>
                          )}
                          {/* Palabras clave */}
                          {article.categories && article.categories.length > 0 && (
                            <Box sx={{ display: 'flex', gap: 0.5, ml: 2, flexWrap: 'wrap' }}>
                              {article.categories.slice(0, 3).map((cat) => (
                                <Chip
                                  key={cat}
                                  label={cat}
                                  size="small"
                                  color="default"
                                  sx={{ mr: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                          {/* PDF y página */}
                          {article.pdf_url && (
                            <Tooltip title="Ver PDF">
                              <IconButton
                                size="small"
                                component="a"
                                href={article.pdf_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{ ml: 1 }}
                                onClick={e => e.stopPropagation()}
                              >
                                <PdfIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          {article.url && (
                            <Tooltip title="Ver en la página de origen">
                              <IconButton
                                size="small"
                                component="a"
                                href={article.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{ ml: 1 }}
                                onClick={e => e.stopPropagation()}
                              >
                                <OpenInNewIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box sx={{ pl: 1 }}>
                            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                              {article.source} | {article.primary_category || ''} {article.version ? `| v${article.version}` : ''}
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{ mb: 1 }}
                              component="span"
                              dangerouslySetInnerHTML={{
                                __html: highlightText(article.abstract, query)
                              }}
                            />
                            <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                {article.authors && Array.isArray(article.authors)
                                  ? article.authors.map(a => a.name).join(', ')
                                  : article.authors}
                              </Typography>
                              {article.doi && (
                                <Chip
                                  label="DOI"
                                  component="a"
                                  href={article.doi}
                                  target="_blank"
                                  clickable
                                  size="small"
                                  sx={{ ml: 1 }}
                                />
                              )}
                              {article.pdf_url && (
                                <Chip
                                  label="PDF"
                                  component="a"
                                  href={article.pdf_url}
                                  target="_blank"
                                  clickable
                                  size="small"
                                  sx={{ ml: 1 }}
                                />
                              )}
                              {article.url && (
                                <Chip
                                  label="Portal"
                                  component="a"
                                  href={article.url}
                                  target="_blank"
                                  clickable
                                  size="small"
                                  sx={{ ml: 1 }}
                                />
                              )}
                              {/* GitHub chip solo si hay link */}
                              {article.github_link && (
                                <Tooltip title={`GitHub: ${article.github_link}`}>
                                  <Chip
                                    icon={<GitHubIcon />}
                                    label={article.github_status === 'OK' ? 'GitHub OK' : (article.github_status === 'Broken' ? 'GitHub Broken' : article.github_status)}
                                    color={article.github_status === 'OK' ? 'success' : (article.github_status === 'Broken' ? 'error' : 'default')}
                                    component="a"
                                    href={article.github_link}
                                    target="_blank"
                                    clickable
                                    size="small"
                                    sx={{ ml: 1 }}
                                  />
                                </Tooltip>
                              )}
                            </Box>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
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
