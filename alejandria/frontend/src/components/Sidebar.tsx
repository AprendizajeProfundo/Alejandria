import React from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Divider, Tooltip, Checkbox, Box } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SourceIcon from '@mui/icons-material/Source';
import SettingsIcon from '@mui/icons-material/Settings';
import HistoryIcon from '@mui/icons-material/History';
import AllInclusiveIcon from '@mui/icons-material/AllInclusive';

const sources = [
  { key: 'arxiv', label: 'Arxiv', icon: <SourceIcon /> },
  { key: 'pubmed', label: 'PubMed', icon: <SourceIcon /> },
  { key: 'wikipedia', label: 'Wikipedia', icon: <SourceIcon /> },
];

export default function Sidebar({ selectedSources, setSelectedSources, open, setOpen, drawerWidth }: {
  selectedSources: string[],
  setSelectedSources: (sources: string[]) => void,
  open: boolean,
  setOpen: (open: boolean) => void,
  drawerWidth: number
}) {
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
  };

  return (
    <Drawer
      variant="persistent"
      open={open}
      PaperProps={{
        sx: {
          width: drawerWidth,
          bgcolor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
          transition: 'width 0.2s',
          zIndex: 1200,
          overflowX: 'hidden'
        }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', p: 1, justifyContent: open ? 'flex-end' : 'center' }}>
        <IconButton onClick={() => setOpen(!open)} size="small" color="primary">
          <MenuIcon />
        </IconButton>
      </Box>
      <Divider />
      <List>
        <Tooltip title="Todas las fuentes" placement="right">
          <ListItem button onClick={handleSelectAll} selected={selectedSources.length === sources.length}>
            <ListItemIcon><AllInclusiveIcon color={selectedSources.length === sources.length ? 'primary' : 'inherit'} /></ListItemIcon>
            {open && <ListItemText primary="Todas las fuentes" />}
            {open && (
              <Checkbox
                checked={selectedSources.length === sources.length}
                tabIndex={-1}
                disableRipple
              />
            )}
          </ListItem>
        </Tooltip>
        {sources.map(source => (
          <Tooltip key={source.key} title={source.label} placement="right">
            <ListItem button onClick={() => handleToggleSource(source.key)} selected={selectedSources.includes(source.key)}>
              <ListItemIcon>{source.icon}</ListItemIcon>
              {open && <ListItemText primary={source.label} />}
              {open && (
                <Checkbox
                  checked={selectedSources.includes(source.key)}
                  tabIndex={-1}
                  disableRipple
                />
              )}
            </ListItem>
          </Tooltip>
        ))}
      </List>
      <Divider />
      <List>
        <Tooltip title="Búsquedas recientes" placement="right">
          <ListItem button>
            <ListItemIcon><HistoryIcon /></ListItemIcon>
            {open && <ListItemText primary="Búsquedas recientes" />}
          </ListItem>
        </Tooltip>
        <Tooltip title="Configuración" placement="right">
          <ListItem button>
            <ListItemIcon><SettingsIcon /></ListItemIcon>
            {open && <ListItemText primary="Configuración" />}
          </ListItem>
        </Tooltip>
      </List>
    </Drawer>
  );
}
