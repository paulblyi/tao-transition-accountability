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
        const rawData = response.data;
        // Ensure arrays exist even if missing
        const safeData: InsightsData = {
          total_facilities: rawData?.total_facilities || 0,
          summary: rawData?.summary || 'No summary available.',
          strengths: Array.isArray(rawData?.strengths) ? rawData.strengths : [],
          challenges: Array.isArray(rawData?.challenges) ? rawData.challenges : [],
          recommendations: Array.isArray(rawData?.recommendations) ? rawData.recommendations : [],
        };
        setData(safeData);
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

  // Safely use arrays (already ensured above)
  const { summary, strengths, challenges, recommendations } = data;

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
        {summary}
      </Typography>

      <Divider sx={{ my: 2 }} />

      {strengths.length > 0 && (
        <>
          <Typography variant="subtitle2" color="success.main" gutterBottom>
            ✅ Strengths
          </Typography>
          <List dense disablePadding>
            {strengths.map((item, idx) => (
              <ListItem key={idx} disableGutters>
                <ListItemText primary={`• ${item}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}

      {challenges.length > 0 && (
        <>
          <Typography variant="subtitle2" color="error.main" gutterBottom sx={{ mt: 2 }}>
            ⚠️ Challenges
          </Typography>
          <List dense disablePadding>
            {challenges.map((item, idx) => (
              <ListItem key={idx} disableGutters>
                <ListItemText primary={`• ${item}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}

      {recommendations.length > 0 && (
        <>
          <Typography variant="subtitle2" color="primary.main" gutterBottom sx={{ mt: 2 }}>
            💡 Recommendations
          </Typography>
          <List dense disablePadding>
            {recommendations.map((item, idx) => (
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