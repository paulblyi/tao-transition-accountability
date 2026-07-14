import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import { getGovernanceInsights } from '../api/client';

interface GovernanceInsightsProps {
  filters: any;
}

interface InsightsData {
  total_facilities: number;
  summary: string;
  strengths: string[];
  challenges: string[];
  recommendations: string[];
}

const GovernanceInsights: React.FC<GovernanceInsightsProps> = ({ filters }) => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getGovernanceInsights(filters);
        setData(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load governance insights');
        console.error('Governance insights error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filters]);

  if (loading) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Governance & Coordination Insights</Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress size={30} />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Governance & Coordination Insights</Typography>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (!data || data.total_facilities === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Governance & Coordination Insights</Typography>
        <Typography variant="body2" color="textSecondary">
          No governance data available for the selected filters.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Governance & Coordination Insights
        </Typography>
        <Chip 
          label={`${data.total_facilities} facility${data.total_facilities > 1 ? 's' : ''}`} 
          size="small" 
          color="primary" 
          variant="outlined"
        />
      </Box>

      <Typography variant="body1" paragraph sx={{ fontStyle: 'italic', bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
        {data.summary}
      </Typography>

      <Divider sx={{ my: 2 }} />

      {data.strengths && data.strengths.length > 0 && (
        <>
          <Typography variant="subtitle2" color="success.main" gutterBottom>
            ✅ Strengths
          </Typography>
          <List dense disablePadding>
            {data.strengths.map((item, idx) => (
              <ListItem key={idx} disableGutters>
                <ListItemText primary={`• ${item}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}

      {data.challenges && data.challenges.length > 0 && (
        <>
          <Typography variant="subtitle2" color="error.main" gutterBottom sx={{ mt: 2 }}>
            ⚠️ Challenges
          </Typography>
          <List dense disablePadding>
            {data.challenges.map((item, idx) => (
              <ListItem key={idx} disableGutters>
                <ListItemText primary={`• ${item}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}

      {data.recommendations && data.recommendations.length > 0 && (
        <>
          <Typography variant="subtitle2" color="primary.main" gutterBottom sx={{ mt: 2 }}>
            💡 Recommendations
          </Typography>
          <List dense disablePadding>
            {data.recommendations.map((item, idx) => (
              <ListItem key={idx} disableGutters>
                <ListItemText primary={`• ${item}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Paper>
  );
};

export default GovernanceInsights;