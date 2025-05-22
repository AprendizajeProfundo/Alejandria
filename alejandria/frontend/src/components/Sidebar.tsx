import React, { useState } from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Divider, Tooltip, Checkbox, Box, Collapse } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SourceIcon from '@mui/icons-material/Source';
import SettingsIcon from '@mui/icons-material/Settings';
import HistoryIcon from '@mui/icons-material/History';
import AllInclusiveIcon from '@mui/icons-material/AllInclusive';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import SelectedArticlesPanel from './SelectedArticlesPanel';
import type { Article } from './SelectedArticlesPanel';

const sources = [
  { key: 'arxiv', label: 'Arxiv', icon: <SourceIcon /> },
  { key: 'pubmed', label: 'PubMed', icon: <SourceIcon /> },
  { key: 'wikipedia', label: 'Wikipedia', icon: <SourceIcon /> },
];

export default function Sidebar({
  selectedSources,
  setSelectedSources,
  open,
  setOpen,
  drawerWidth,
  selectedArticles,
  setSelectedArticles,
}: {
  selectedSources: string[],
  setSelectedSources: (sources: string[]) => void,
  open: boolean,
  setOpen: (open: boolean) => void,
  drawerWidth: number,
  selectedArticles: Article[],
  setSelectedArticles: React.Dispatch<React.SetStateAction<Article[]>>
}) {
  const [sourcesOpen, setSourcesOpen] = useState(open);

  React.useEffect(() => {
    if (open) setSourcesOpen(true);
    else setSourcesOpen(false);
  }, [open]);

  const handleToggleSource = (key: string) => {
    if (selectedSources.includes(key)) {
      setSelectedSources(selectedSources.filter(s => s !== key));
    } else {
      setSelectedSources([...selectedSources, key]);
    }
  };

  const handleSelectAll = () => {
    if (selectedSources.length === sources.length) {
      setSelectedSources([]);
    } else {
      setSelectedSources(sources.map(s => s.key));
    }
    setSourcesOpen(true);
  };

  const handleCollapsedAllClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setOpen(true);
    setSourcesOpen(true);
  };

  // Hacer toda la caja de la hamburguesa clickeable
  const handleHamburgerClick = () => setOpen(!open);

  // Mostrar el panel solo si hay artículos seleccionados
  const showSelectedPanel = selectedArticles && selectedArticles.length > 0;
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Drawer
      variant="permanent"
      open={open}
      PaperProps={{
        sx: {
          width: open ? drawerWidth : 56,
          bgcolor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
          transition: 'width 0.5s',
          zIndex: 1200,
          overflowX: 'hidden',
          boxSizing: 'border-box',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
      ModalProps={{
        keepMounted: true,
      }}
    >
      {/* Hamburguesa arriba, toda la caja clickeable */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: 64,
          width: '100%',
          mb: 1,
          cursor: 'pointer',
          userSelect: 'none',
          '&:hover': {
            bgcolor: 'action.hover'
          }
        }}
        onClick={handleHamburgerClick}
        tabIndex={0}
        role="button"
        aria-label="Expandir/collapse menú"
      >
        <MenuIcon sx={{
          fontSize: 28,
          color: 'primary.main',
          transition: 'transform 0.2s',
          ...(open && { transform: 'rotate(90deg)' })
        }} />
      </Box>
      <Divider />
      <List>
        <Tooltip title="Fuentes" placement="right">
          <ListItem
            button
            onClick={open ? handleSelectAll : handleCollapsedAllClick}
            selected={selectedSources.length === sources.length}
            sx={{
              pl: open ? 2 : 0,
              pr: open ? 2 : 0,
              justifyContent: 'center',
              minHeight: 48,
              height: 48,
              width: '100%',
              overflow: 'hidden',
              alignItems: 'center'
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: open ? 2 : 0,
                justifyContent: 'center',
                alignItems: 'center',
                display: 'flex'
              }}
            >
              <AllInclusiveIcon
                color={selectedSources.length === sources.length ? 'primary' : 'inherit'}
                sx={{ fontSize: 28 }}
              />
            </ListItemIcon>
            {open && (
              <ListItemText
                primary="Fuentes"
                primaryTypographyProps={{
                  noWrap: true,
                  sx: {
                    fontWeight: 600,
                    fontSize: 17,
                    letterSpacing: 0.2,
                    color: theme => theme.palette.text.primary,
                    lineHeight: 1.2,
                  }
                }}
                sx={{
                  m: 0,
                  minWidth: 0,
                  maxWidth: '100%',
                  overflow: 'hidden'
                }}
              />
            )}
            {open && (
              <Checkbox
                checked={selectedSources.length === sources.length}
                tabIndex={-1}
                disableRipple
                sx={{ ml: 1, p: 0.5 }}
              />
            )}
            {open && (
              <IconButton
                size="small"
                onClick={e => {
                  e.stopPropagation();
                  setSourcesOpen(prev => !prev);
                }}
                sx={{ ml: 1 }}
              >
                {sourcesOpen ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            )}
          </ListItem>
        </Tooltip>
        <Collapse in={sourcesOpen && open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {sources.map(source => (
              <Tooltip key={source.key} title={source.label} placement="right">
                <ListItem
                  button
                  onClick={() => handleToggleSource(source.key)}
                  selected={selectedSources.includes(source.key)}
                  sx={{
                    pl: 4,
                    minHeight: 40,
                    height: 40,
                    alignItems: 'center'
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 0, mr: 1.5, justifyContent: 'center', alignItems: 'center', display: 'flex' }}>
                    {source.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={source.label}
                    primaryTypographyProps={{
                      noWrap: true,
                      sx: { fontSize: 15 }
                    }}
                    sx={{ m: 0, minWidth: 0 }}
                  />
                  <Checkbox
                    checked={selectedSources.includes(source.key)}
                    tabIndex={-1}
                    disableRipple
                    sx={{ ml: 1, p: 0.5 }}
                  />
                </ListItem>
              </Tooltip>
            ))}
          </List>
        </Collapse>
      </List>
      <Divider />
      <List>
        <Tooltip title="Búsquedas recientes" placement="right">
          <ListItem button sx={{
            minHeight: 48,
            height: 48,
            justifyContent: 'center',
            alignItems: 'center',
            pl: open ? 2 : 0,
            pr: open ? 2 : 0
          }}>
            <ListItemIcon sx={{
              minWidth: 0,
              mr: open ? 2 : 0,
              justifyContent: 'center',
              alignItems: 'center',
              display: 'flex'
            }}>
              <HistoryIcon sx={{ fontSize: 28 }} />
            </ListItemIcon>
            {open && <ListItemText primary="Búsquedas recientes" primaryTypographyProps={{ noWrap: true, fontSize: 16, fontWeight: 500 }} />}
          </ListItem>
        </Tooltip>
        <Tooltip title="Configuración" placement="right">
          <ListItem button sx={{
            minHeight: 48,
            height: 48,
            justifyContent: 'center',
            alignItems: 'center',
            pl: open ? 2 : 0,
            pr: open ? 2 : 0
          }}>
            <ListItemIcon sx={{
              minWidth: 0,
              mr: open ? 2 : 0,
              justifyContent: 'center',
              alignItems: 'center',
              display: 'flex'
            }}>
              <SettingsIcon sx={{ fontSize: 28 }} />
            </ListItemIcon>
            {open && <ListItemText primary="Configuración" primaryTypographyProps={{ noWrap: true, fontSize: 16, fontWeight: 500 }} />}
          </ListItem>
        </Tooltip>
      </List>
      {/* Panel de artículos seleccionados, visible solo si hay selección, SIEMPRE en la parte inferior */}
      <Box sx={{
        mt: 'auto',
        mb: 1,
        px: open ? 1 : 0,
        width: '100%',
        minHeight: showSelectedPanel && open && !collapsed ? 80 : 0,
        transition: 'all 0.3s cubic-bezier(.4,0,.2,1)',
        opacity: showSelectedPanel && open && !collapsed ? 1 : 0.5,
        pointerEvents: showSelectedPanel && open ? 'auto' : 'none',
        position: 'relative'
      }}>
        {(showSelectedPanel && open && !collapsed) ? (
          <>
            <SelectedArticlesPanel
              selectedArticles={selectedArticles}
              setSelectedArticles={setSelectedArticles}
              sidebarMode
              onExpandPanel={() => setCollapsed(false)}
            />
            {/* Botón para colapsar, solo abajo y visible */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
              <IconButton
                size="small"
                onClick={() => setCollapsed(true)}
                sx={{
                  bgcolor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  boxShadow: 1,
                  transition: 'transform 0.2s',
                }}
                title="Ocultar artículos seleccionados"
              >
                <ExpandMore />
              </IconButton>
            </Box>
          </>
        ) : null}
        {/* Botón para expandir cuando está colapsado */}
        {(showSelectedPanel && open && collapsed) && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
            <IconButton
              size="small"
              onClick={() => setCollapsed(false)}
              sx={{
                bgcolor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                boxShadow: 1,
                transition: 'transform 0.2s',
              }}
              title="Mostrar artículos seleccionados"
            >
              <ExpandLess />
            </IconButton>
          </Box>
        )}
      </Box>
    </Drawer>
  );
}
