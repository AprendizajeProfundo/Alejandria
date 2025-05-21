import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import SearchPage from './pages/SearchPage';
import NotebookPage from './pages/NotebookPage';
import '@fontsource/roboto-mono/400.css';

// Paleta azul futurista y detalles visuales
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
      dark: '#0a1929',
      light: '#64b5f6',
      contrastText: '#fff'
    },
    secondary: {
      main: '#00e5ff',
      contrastText: '#fff'
    },
    background: {
      default: '#101624',
      paper: '#161d2a'
    },
    divider: '#22304a'
  },
  typography: {
    fontFamily: '"Roboto Mono", "Roboto", "Arial", sans-serif',
    h5: {
      fontWeight: 700,
      letterSpacing: '0.05em'
    }
  },
  shape: {
    borderRadius: 14
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 10
        }
      }
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none'
        }
      }
    },
    MuiAutocomplete: {
      styleOverrides: {
        option: {
          backgroundColor: '#161d2a',
          '&[aria-selected="true"]': {
            backgroundColor: '#22304a',
          },
          '&:hover': {
            backgroundColor: '#22304a',
          }
        },
        paper: {
          backgroundColor: '#161d2a',
        }
      }
    }
  }
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/notebook" element={<NotebookPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
