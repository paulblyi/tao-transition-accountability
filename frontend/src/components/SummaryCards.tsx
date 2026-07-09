import React from 'react';
import { Grid, Card, CardContent, Typography } from '@mui/material';
import { AggregatedData } from '../types';

const SummaryCards: React.FC<{ data: AggregatedData | null }> = ({ data }) => {
  if (!data) return <Typography>Loading summary...</Typography>;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={4}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Facilities
            </Typography>
            <Typography variant="h4">{data.total_facilities}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={4}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Avg. HTS MOHCC (%)
            </Typography>
            <Typography variant="h4">
              {data.avg_hts_mohcc_pct != null ? data.avg_hts_mohcc_pct.toFixed(1) : '—'}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={4}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Avg. VL MOHCC (%)
            </Typography>
            <Typography variant="h4">
              {data.avg_vl_mohcc_pct != null ? data.avg_vl_mohcc_pct.toFixed(1) : '—'}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default SummaryCards;
