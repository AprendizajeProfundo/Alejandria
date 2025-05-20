import React from 'react';
import { Box, Typography } from '@mui/material';

const NotebookPage: React.FC = () => {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        Cuaderno de Notas
      </Typography>
      <Typography variant="body1">
        Esta funcionalidad está en desarrollo.
      </Typography>
    </Box>
  );
};

export default NotebookPage;
