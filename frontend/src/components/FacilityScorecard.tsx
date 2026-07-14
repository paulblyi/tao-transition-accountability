import React from 'react';
import {
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Box,
} from '@mui/material';

interface Props {
  data: any[];
  maxItems?: number;
}

const FacilityScorecard: React.FC<Props> = ({ data, maxItems = 6 }) => {
  if (!data || data.length === 0) {
    return <Typography>No facility data available.</Typography>;
  }

  const getStatus = (value: number) => {
    if (value >= 80) return { color: 'success', label: 'Good' };
    if (value >= 50) return { color: 'warning', label: 'Moderate' };
    return { color: 'error', label: 'Needs Improvement' };
  };

  const sorted = [...data]
    .filter(d => d.hts_mohcc_pct !== undefined)
    .sort((a, b) => (b.hts_mohcc_pct || 0) - (a.hts_mohcc_pct || 0))
    .slice(0, maxItems);

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Top Facilities – HTS Performance</Typography>
      <Grid container spacing={2}>
        {sorted.map((facility, idx) => (
          <Grid item xs={12} sm={6} md={4} key={idx}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle2" noWrap>
                  {facility.facility || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {facility.district || ''}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip
                    label={`HTS: ${facility.hts_mohcc_pct || 0}%`}
                    size="small"
                    color={getStatus(facility.hts_mohcc_pct || 0).color as any}
                  />
                  {facility.vl_mohcc_pct !== undefined && (
                    <Chip
                      label={`VL: ${facility.vl_mohcc_pct || 0}%`}
                      size="small"
                      sx={{ ml: 1 }}
                      color={getStatus(facility.vl_mohcc_pct || 0).color as any}
                    />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
};

export default FacilityScorecard;