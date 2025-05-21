import React from 'react';
import { AppBar, Toolbar, Typography } from '@mui/material';

export default function Topbar() {
  return (
    <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider', backdropFilter: 'blur(6px)' }}>
      <Toolbar sx={{ minHeight: 64, px: 2, gap: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: 2, color: 'primary.main', mr: 3 }}>
          Alejandría
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
