import React from 'react';
import { Grid, Card, CardContent, Typography, Chip } from '@mui/material';

interface Props {
  facilities: any[];
}

const FacilityScorecard: React.FC<Props> = ({ facilities }) => {
  const getStatus = (pct: number) => {
    if (pct >= 80) return { color: 'success', label: 'Excellent' };
    if (pct >= 60) return { color: 'warning', label: 'Good' };
    return { color: 'error', label: 'Needs Improvement' };
  };

  return (
    <Grid container spacing={2}>
      {facilities.slice(0, 6).map((f, idx) => (
        <Grid item xs={12} sm={6} md={4} key={idx}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" noWrap>{f.facility}</Typography>
              <Typography variant="body2" color="textSecondary">
                {f.district}, {f.province}
              </Typography>
              <Chip 
                label={`HTS: ${f.hts_mohcc_pct || 0}%`} 
                size="small" 
                color={getStatus(f.hts_mohcc_pct || 0).color as any}
                sx={{ mt: 1, mr: 0.5 }}
              />
              <Chip 
                label={`VL: ${f.vl_mohcc_pct || 0}%`} 
                size="small" 
                color={getStatus(f.vl_mohcc_pct || 0).color as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};