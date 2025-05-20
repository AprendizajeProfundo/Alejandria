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
import { SearchResults } from '../components/SearchResults';

const drawerWidth = 280;

const StyledDrawer = styled(Drawer)(({ theme }) => ({
  width: drawerWidth,
  flexShrink: 0,
  whiteSpace: 'nowrap',
  '& .MuiDrawer-paper': {
    width: drawerWidth,
    background: theme.palette.background.paper,
    borderRight: `1px solid ${theme.palette.divider}`,
    boxSizing: 'border-box',
    overflowX: 'hidden',
    '&::-webkit-scrollbar': {
      width: '6px',
    },
    '&::-webkit-scrollbar-thumb': {
      backgroundColor: theme.palette.action.hover,
      borderRadius: '4px',
    },
    '&::-webkit-scrollbar-track': {
      backgroundColor: 'transparent',
    },
  },
  '& .MuiBackdrop-root': {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
}));

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  zIndex: theme.zIndex.drawer + 1,
  background: theme.palette.mode === 'dark' ? '#121212' : '#1976d2',
  boxShadow: 'none',
  borderBottom: `1px solid ${theme.palette.divider}`,
}));

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  padding: theme.spacing(0, 2),
}));

const StyledListItem = styled(ListItemButton)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  margin: theme.spacing(0.5, 1.5),
  padding: theme.spacing(1, 2),
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
  '&.Mui-selected': {
    backgroundColor: theme.palette.action.selected,
    '&:hover': {
      backgroundColor: theme.palette.action.selected,
    },
  },
}));

const UserProfile = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(2),
  borderBottom: `1px solid ${theme.palette.divider}`,
  marginBottom: theme.spacing(1),
}));

const NavSection = ({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) => {
  const [open, setOpen] = useState(true);
  
  return (
    <>
      <ListItemButton onClick={() => setOpen(!open)}>
        <ListItemIcon sx={{ minWidth: 36 }}>{icon}</ListItemIcon>
        <ListItemText primary={title} />
        {open ? <ExpandLess /> : <ExpandMore />}
      </ListItemButton>
      <Collapse in={open} timeout="auto" unmountOnExit>
        {children}
      </Collapse>
    </>
  );
};

// Definir tipos para los mensajes del WebSocket
type SearchError = {
  message: string;
  type: 'CONNECTION' | 'PARSING' | 'NETWORK' | 'SERVER';
};

interface SearchResult {
  id: string;
  title: string;
  abstract: string;
  published: string;
  authors: Array<{ name: string }>;
  url: string;
  pdf_url?: string;
  source: string;
  relevance?: number;
  categories?: string[];
}

const SearchPage: React.FC = (): React.ReactElement => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [selectedSources, setSelectedSources] = useState<{[key: string]: boolean}>({
    arxiv: true,
    tds: true
  });
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

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleSourceToggle = (sourceId: string) => {
    setSelectedSources(prev => ({
      ...prev,
      [sourceId]: !prev[sourceId]
    }));
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

  const drawerContent = (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      transition: 'width 0.3s ease',
      width: sidebarCollapsed ? 72 : 280,
      overflow: 'hidden',
      bgcolor: 'background.paper',
      borderRight: `1px solid ${theme.palette.divider}`
    }}>
      {/* Botón de colapsar */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'flex-end',
        p: 1,
        borderBottom: `1px solid ${theme.palette.divider}`
      }}>
        <IconButton 
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          size="small"
        >
          {sidebarCollapsed ? <ExpandMore /> : <ExpandLess />}
        </IconButton>
      </Box>
      
      {/* Contenido del panel */}
      <Box sx={{ 
        overflowY: 'auto',
        flexGrow: 1,
        p: 1,
        '&::-webkit-scrollbar': {
          width: '4px',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: theme.palette.action.hover,
          borderRadius: '4px',
        },
      }}>
        <Box sx={{ display: sidebarCollapsed ? 'none' : 'block' }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'medium' }}>
            Fuentes de Búsqueda
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            {availableSources.map((source) => (
              <Box 
                key={source.id}
                onClick={() => handleSourceToggle(source.id)}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1,
                  borderRadius: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                  bgcolor: selectedSources[source.id] ? 'action.selected' : 'transparent',
                  mb: 0.5,
                }}
              >
                <Checkbox 
                  checked={selectedSources[source.id]}
                  size="small"
                  sx={{ p: 0.5, mr: 1 }}
                />
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ mr: 1, display: 'flex', color: 'text.secondary' }}>
                    {source.icon}
                  </Box>
                  <Typography variant="body2">
                    {source.name}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
          
          <TextField
            fullWidth
            size="small"
            placeholder="Buscar..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton 
                    size="small"
                    onClick={() => setSearchQuery('')}
                    edge="end"
                  >
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
              sx: {
                bgcolor: 'background.paper',
                '& input': {
                  py: 1,
                },
              },
            }}
            sx={{ mb: 2 }}
          />
          
          <Button
            fullWidth
            variant="contained"
            onClick={handleSearch}
            disabled={isSearching || !searchQuery.trim()}
            startIcon={isSearching ? <CircularProgress size={20} /> : <SearchIcon />}
          >
            {isSearching ? 'Buscando...' : 'Buscar'}
          </Button>
        </Box>
        
        {/* Versión colapsada */}
        <Box sx={{ display: sidebarCollapsed ? 'block' : 'none', p: 1 }}>
          {availableSources.map((source) => (
            <Tooltip key={source.id} title={source.name} placement="right">
              <IconButton
                onClick={() => handleSourceToggle(source.id)}
                color={selectedSources[source.id] ? 'primary' : 'default'}
                sx={{
                  mb: 1,
                  bgcolor: selectedSources[source.id] ? 'action.selected' : 'transparent',
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                }}
              >
                {React.cloneElement(source.icon, { fontSize: 'small' })}
              </IconButton>
            </Tooltip>
          ))}
          
          <Divider sx={{ my: 1 }} />
          
          <Tooltip title="Buscar" placement="right">
            <span>
              <IconButton
                onClick={() => {
                  setSidebarCollapsed(false);
                  setTimeout(() => {
                    document.getElementById('search-input')?.focus();
                  }, 300);
                }}
                disabled={!searchQuery.trim()}
                color="primary"
              >
                <SearchIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* AppBar */}
      <StyledAppBar position="fixed" sx={{ 
        width: { md: `calc(100% - ${sidebarCollapsed ? 72 : 280}px)` },
        ml: { md: `${sidebarCollapsed ? 72 : 280}px` },
        transition: theme.transitions.create(['width', 'margin'], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }),
      }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center',
            flexGrow: 1,
            maxWidth: 800,
            mx: 'auto'
          }}>
            <LibraryBooksIcon sx={{ mr: 1, color: 'primary.contrastText' }} />
            <Typography variant="h6" noWrap component="div" sx={{ color: 'primary.contrastText' }}>
              Alejandría
            </Typography>
            
            <Box sx={{ flexGrow: 1, ml: 4, display: { xs: 'none', sm: 'block' } }}>
              <TextField
                id="search-input"
                fullWidth
                size="small"
                placeholder="Buscar artículos académicos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery && (
                    <InputAdornment position="end">
                      <IconButton 
                        size="small"
                        onClick={() => setSearchQuery('')}
                        edge="end"
                      >
                        <ClearIcon fontSize="small" />
                      </IconButton>
                    </InputAdornment>
                  ),
                  sx: {
                    bgcolor: 'background.paper',
                    '& input': {
                      py: 1,
                    },
                  },
                }}
              />
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title="Búsqueda avanzada">
              <IconButton color="inherit" sx={{ display: { sm: 'none' } }}>
                <SearchIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Notificaciones">
              <IconButton color="inherit">
                <StarIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </StyledAppBar>
      
      {/* Sidebar */}
      <Box 
        component="nav"
        sx={{
          width: { md: sidebarCollapsed ? 72 : 280 },
          flexShrink: { md: 0 },
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          zIndex: theme.zIndex.drawer + 1,
        }}
      >
        <StyledDrawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', md: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box',
              width: { md: sidebarCollapsed ? 72 : 280 },
              borderRight: 'none',
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.leavingScreen,
              }),
            },
          }}
        >
          {drawerContent}
        </StyledDrawer>
      </Box>
      
      {/* Contenido principal */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { 
            xs: '100%',
            md: `calc(100% - ${sidebarCollapsed ? 72 : 280}px)` 
          },
          mt: { xs: 7, sm: 8 },
          ml: { 
            xs: 0,
            md: `${sidebarCollapsed ? 72 : 280}px` 
          },
          minHeight: '100vh',
          backgroundColor: theme.palette.background.default,
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Container 
          maxWidth="xl" 
          sx={{ 
            mt: 2,
            width: '100%',
            maxWidth: '100% !important',
            px: { xs: 0, sm: 2 },
          }}
        >
          <SearchResults />
        </Container>
      </Box>
      
      {/* Snackbar para notificaciones */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbar.severity} 
          sx={{ width: '100%' }}
          elevation={6}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
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

export default SearchPage;
