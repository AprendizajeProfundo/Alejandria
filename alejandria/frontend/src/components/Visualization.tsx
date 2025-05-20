import React from 'react';
import { Box, Card, CardContent, Typography, Grid, Paper } from '@mui/material';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { useTheme } from '@mui/material/styles';

ChartJS.register(ArcElement, Tooltip, Legend);

export interface VisualizationData {
  type: string;
  relevance?: number;
  visualizations?: Record<string, number>;
  title?: string;
  content?: string;
}

interface VisualizationProps {
  data: VisualizationData;
  width?: number;
  height?: number;
}

const Visualization: React.FC<VisualizationProps> = ({ data, width = 200, height = 200 }) => {
  const theme = useTheme();

  const getVisualization = () => {
    if (!data) return null;

    switch (data.type) {
      case 'relevance':
        if (!data.relevance) return null;
        return (
          <Pie
            data={{
              labels: ['Relevancia'],
              datasets: [{
                data: [data.relevance * 100, 100 - (data.relevance * 100)],
                backgroundColor: [theme.palette.primary.main, theme.palette.grey[200]],
              }],
            }}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top',
                },
                tooltip: {
                  enabled: true,
                },
              },
            }}
          />
        );
      case 'source_distribution':
        if (!data.visualizations) return null;
        return (
          <Pie
            data={{
              labels: Object.keys(data.visualizations),
              datasets: [{
                data: Object.values(data.visualizations),
                backgroundColor: [
                  theme.palette.primary.main,
                  theme.palette.secondary.main,
                  theme.palette.success.main,
                  theme.palette.warning.main,
                  theme.palette.error.main,
                ].slice(0, Object.keys(data.visualizations).length),
              }],
            }}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  position: 'top',
                },
                tooltip: {
                  enabled: true,
                },
              },
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {data.title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {data.content}
        </Typography>
        <Box sx={{ width: width, height: height }}>
          {getVisualization()}
        </Box>
      </CardContent>
    </Card>
  );
};

export default Visualization;
