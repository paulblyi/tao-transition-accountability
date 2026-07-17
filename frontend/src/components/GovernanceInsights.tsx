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

interface Props {
  filters: any;
  enabled: boolean;
}

interface InsightsData {
  total_facilities: number;
  summary: string;
  strengths: string[];
  challenges: string[];
  recommendations: string[];
  llm_failed?: boolean;
}

const GovernanceInsights: React.FC<Props> = ({ filters, enabled }) => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Always fetch – skip_llm = NOT enabled
        const response = await getGovernanceInsights(filters, !enabled);
        const raw = response.data;
        setData({
          total_facilities: raw.total_facilities || 0,
          summary: raw.summary || 'No summary available.',
          // Ensure every item is a string (safeguard against objects)
          strengths: Array.isArray(raw.strengths)
            ? raw.strengths.map((s: any) => typeof s === 'string' ? s : String(s))
            : [],
          challenges: Array.isArray(raw.challenges)
            ? raw.challenges.map((c: any) => typeof c === 'string' ? c : String(c))
            : [],
          recommendations: Array.isArray(raw.recommendations)
            ? raw.recommendations.map((r: any) => typeof r === 'string' ? r : String(r))
            : [],
          llm_failed: raw.llm_failed || false,
        });
      } catch (err: any) {
        setError(err.message || 'Failed to load governance insights');
        console.error('Governance insights error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filters, enabled]);

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

  const { summary, strengths, challenges, recommendations, llm_failed } = data;

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
        {llm_failed && (
          <Chip
            label="AI unavailable – showing data summary"
            size="small"
            color="warning"
            sx={{ ml: 1 }}
          />
        )}
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