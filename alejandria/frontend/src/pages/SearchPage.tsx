import React, { useState } from 'react';
import { 
  Box, 
  Container,
  CssBaseline,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Snackbar,
  useTheme,
  useMediaQuery,
  Alert,
  Collapse,
  ListItemButton,
  styled,
  alpha,
  Avatar,
  Tooltip,
  Chip,
  TextField,
  Button,
  Checkbox,
  InputAdornment,
  CircularProgress
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Settings as SettingsIcon,
  Home as HomeIcon,
  Bookmark as BookmarkIcon,
  History as HistoryIcon,
  Help as HelpIcon,
  ExpandLess,
  ExpandMore,
  Dashboard as DashboardIcon,
  Science as ScienceIcon,
  School as SchoolIcon,
  LibraryBooks as LibraryBooksIcon,
  Star as StarIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
  Clear as ClearIcon,
  CheckBox as CheckBoxIcon,
  CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon
} from '@mui/icons-material';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';
import { SearchResults } from '../components/SearchResults';
import { Article } from '../components/SelectedArticlesPanel';

const DRAWER_WIDTH_OPEN = 266;
const DRAWER_WIDTH_COLLAPSED = 64;

export default function SearchPage() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedSources, setSelectedSources] = useState<string[]>(['arxiv', 'pubmed', 'wikipedia']);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({ open: false, message: '', severity: 'info' });
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const [collectionsOpen, setCollectionsOpen] = useState(true);
  const [selectedArticles, setSelectedArticles] = useState<Article[]>([]);

  const drawerWidth = sidebarOpen ? DRAWER_WIDTH_OPEN : DRAWER_WIDTH_COLLAPSED;

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Cambia la función para trabajar con string[] en vez de objeto
  const handleToggleSource = (sourceId: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(s => s !== sourceId)
        : [...prev, sourceId]
    );
  };
  
  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    // Aquí iría la lógica para realizar la búsqueda
    console.log('Buscando:', searchQuery, 'en fuentes:', 
      Object.entries(selectedSources)
        .filter(([_, selected]) => selected)
        .map(([id]) => id)
    );
    
    // Simular búsqueda
    setTimeout(() => {
      setIsSearching(false);
      showSnackbar('Búsqueda completada', 'success');
    }, 2000);
  };

  const availableSources = [
    { id: 'arxiv', name: 'ArXiv', icon: <ScienceIcon /> },
    { id: 'tds', name: 'Towards Data Science', icon: <SchoolIcon /> },
  ];

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
      <Sidebar
        selectedSources={selectedSources}
        setSelectedSources={setSelectedSources}
        open={sidebarOpen}
        setOpen={setSidebarOpen}
        drawerWidth={drawerWidth}
        selectedArticles={selectedArticles}
        setSelectedArticles={setSelectedArticles}
      />
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          ml: `${drawerWidth}px`,
          transition: 'margin-left 0.2s'
        }}
      >
        <Topbar />
        <Box sx={{ flex: 1, p: 4, overflow: 'auto' }}>
          <SearchResults
            selectedArticles={selectedArticles}
            setSelectedArticles={setSelectedArticles}
          />
        </Box>
      </Box>
    </Box>
  );
};

// @ts-ignore - Ignorar errores de tipo para el tema
declare module '@mui/material/styles' {
  interface Theme {
    breakpoints: {
      down: (key: string | number) => string;
    };
  }
}
