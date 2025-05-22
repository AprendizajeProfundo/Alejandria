import React, { useState } from 'react';
import { Box, Paper, Typography, Button, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Chip, IconButton } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CloseIcon from '@mui/icons-material/Close';
import extractionService from '../services/extractionService';

// Usa el mismo tipo que SearchResult para evitar incompatibilidades
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
}

const SelectedArticlesPanel: React.FC<Props> = ({ selectedArticles, setSelectedArticles }) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, any>>({});

  const handleExtract = async () => {
    setLoading(true);
    const newResults: Record<string, any> = {};
    for (const art of selectedArticles) {
      try {
        const res = await extractionService.extractIdeas(art);
        newResults[art.id] = res;
      } catch (e) {
        newResults[art.id] = { error: 'Error al extraer ideas' };
      }
    }
    setResults(newResults);
    setLoading(false);
  };

  if (!selectedArticles.length) return null;

  return (
    <Paper elevation={3} sx={{ p: 2, maxWidth: 1200, mx: 'auto', mb: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ flex: 1 }}>Artículos seleccionados ({selectedArticles.length})</Typography>
        <IconButton
          size="small"
          onClick={() => setSelectedArticles([])}
          sx={{ ml: 2 }}
          title="Limpiar selección"
        >
          <CloseIcon />
        </IconButton>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        {selectedArticles.map((art, idx) => (
          <Chip
            key={art.id}
            label={`${idx + 1}. ${art.title}`}
            onDelete={() => setSelectedArticles(selectedArticles.filter(a => a.id !== art.id))}
            sx={{ maxWidth: 300 }}
          />
        ))}
      </Box>
      <Button
        variant="contained"
        onClick={handleExtract}
        disabled={loading || !selectedArticles.length}
        startIcon={loading ? <CircularProgress size={18} /> : null}
        sx={{ mb: 2 }}
      >
        Extraer Ideas y Conceptos
      </Button>
      <Box>
        {Object.entries(results).map(([id, res]) => (
          <Accordion key={id} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                {selectedArticles.find(a => a.id === id)?.title}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {res?.error ? (
                <Typography color="error">{res.error}</Typography>
              ) : (
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(res, null, 2)}
                </pre>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </Paper>
  );
};

export default SelectedArticlesPanel;
