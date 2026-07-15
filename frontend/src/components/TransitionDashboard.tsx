import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Box,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { getCoverage, getTransitionRisk, getRiskNarrative } from '../api/client';

interface Props {
  filters: any;
}

const TransitionDashboard: React.FC<Props> = ({ filters }) => {
  const [coverage, setCoverage] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [narrative, setNarrative] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [covRes, riskRes, narrativeRes] = await Promise.all([
          getCoverage(filters),
          getTransitionRisk(filters),
          getRiskNarrative(filters),
        ]);
        setCoverage(covRes.data);
        setRisk(riskRes.data);
        setNarrative(narrativeRes.data.narrative);
      } catch (err: any) {
        setError(err.message || 'Failed to load transition data');
        console.error('Transition data error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filters]);

  if (loading) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Transition Dashboard</Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress size={30} />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Transition Dashboard</Typography>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (!coverage || coverage.total_facilities === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Transition Dashboard</Typography>
        <Typography variant="body2" color="textSecondary">
          No data available for the selected filters.
        </Typography>
      </Paper>
    );
  }

  // Prepare risk pie chart data
  const riskData = risk ? [
    { name: 'High Risk', value: risk.high_risk || 0 },
    { name: 'Medium Risk', value: risk.medium_risk || 0 },
    { name: 'Low Risk', value: risk.low_risk || 0 },
  ] : [];
  const COLORS = ['#D32F2F', '#FFA726', '#4CAF50'];

  // Top high-risk facilities
  const highRiskFacilities = risk?.facilities?.filter((r: any) => r.risk_level === 'High') || [];

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Transition Dashboard – Accountability & Readiness</Typography>

      <Grid container spacing={3}>
        {/* Coverage cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4">{coverage.percentage_covered || 0}%</Typography>
              <Typography variant="body2" color="textSecondary">District Coverage</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4">{coverage.tracked_in_last_30_days || 0}</Typography>
              <Typography variant="body2" color="textSecondary">Facilities Tracked (Last 30 Days)</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="error">{coverage.not_tracked_recently?.length || 0}</Typography>
              <Typography variant="body2" color="textSecondary">Facilities Not Tracked Recently</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="warning.main">{risk?.high_risk || 0}</Typography>
              <Typography variant="body2" color="textSecondary">High Risk Facilities</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Pie Chart + Narrative side by side */}
        <Grid item xs={12} md={6}>
          <Box sx={{ height: 250 }}>
            <Typography variant="subtitle2" gutterBottom>Transition Risk Distribution</Typography>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        </Grid>

        {/* Narrative box */}
        <Grid item xs={12} md={6}>
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Typography variant="subtitle2" gutterBottom>📋 Accountability & Readiness Narrative</Typography>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                bgcolor: '#f5f5f5',
                borderRadius: 2,
                minHeight: 120,
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <Typography variant="body2" fontStyle="italic">
                {narrative || 'Loading narrative...'}
              </Typography>
            </Paper>
          </Box>
        </Grid>

        {/* Priority facilities (not tracked recently) */}
        {coverage.not_tracked_recently && coverage.not_tracked_recently.length > 0 && (
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>⚠️ Priority Facilities to Track</Typography>
            <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
              <List dense>
                {coverage.not_tracked_recently.slice(0, 5).map((item: any) => (
                  <ListItem key={item.facility}>
                    <ListItemText
                      primary={item.facility}
                      secondary={item.days_since ? `Last visit: ${item.days_since} days ago` : 'Never visited'}
                    />
                    <Chip
                      label={item.days_since && item.days_since > 60 ? 'Urgent' : 'Overdue'}
                      size="small"
                      color={item.days_since && item.days_since > 60 ? 'error' : 'warning'}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Grid>
        )}

        {/* High-risk facilities */}
        {highRiskFacilities.length > 0 && (
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom color="error">🔴 High-Risk Facilities – Urgent Action Required</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {highRiskFacilities.slice(0, 5).map((r: any) => (
                <Chip
                  key={r.facility}
                  label={`${r.facility} (score: ${r.risk_score})`}
                  color="error"
                  size="medium"
                />
              ))}
            </Box>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default TransitionDashboard;