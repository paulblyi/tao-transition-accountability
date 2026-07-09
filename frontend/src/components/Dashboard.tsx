import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography } from '@mui/material';
import Filters from './Filters';
import SummaryCards from './SummaryCards';
import QuantitativeCharts from './QuantitativeCharts';
import QualitativeInsights from './QualitativeInsights';
import { getAggregatedData, getInsights } from '../api/client';
import { Filters as FiltersType, AggregatedData, Insight } from '../types';

const Dashboard: React.FC = () => {
  const [filters, setFilters] = useState<FiltersType>({});
  const [aggregated, setAggregated] = useState<AggregatedData | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const aggRes = await getAggregatedData(filters);
        setAggregated(aggRes.data);
        const insRes = await getInsights(filters);
        setInsights(insRes.data.insights);
      } catch (error) {
        console.error('Error fetching data', error);
      }
    };
    fetchData();
  }, [filters]);

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      <Filters onFilterChange={setFilters} />
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <SummaryCards data={aggregated} />
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <QuantitativeCharts data={aggregated} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <QualitativeInsights insights={insights} />
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
