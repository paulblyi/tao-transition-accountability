import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper } from '@mui/material';
import Filters from './Filters';
import SummaryCards from './SummaryCards';
import QuantitativeCharts from './QuantitativeCharts';
import QualitativeInsights from './QualitativeInsights';
import { getAggregatedData, getInsights, getTableData } from '../api/client';
import { Filters as FiltersType, AggregatedData, Insight } from '../types';
import DataTable from './DataTable';
import TrendChart from './TrendChart';

// Define type for aggregated insight (matches the component's prop)
type AggregatedInsight = Insight & {
  facilities?: string;
  total_facilities?: number;
};

const Dashboard: React.FC = () => {
  const [filters, setFilters] = useState<FiltersType>({});
  const [aggregated, setAggregated] = useState<AggregatedData | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [aggregatedInsights, setAggregatedInsights] = useState<AggregatedInsight | undefined>(undefined);
  const [tableData, setTableData] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [aggRes, insRes, tableRes] = await Promise.all([
          getAggregatedData(filters),
          getInsights(filters),
          getTableData(filters),
        ]);
        setAggregated(aggRes.data);
        setInsights(insRes.data.insights || []);
        setAggregatedInsights(insRes.data.aggregated || undefined);
        setTableData(tableRes.data || []);
      } catch (error) {
        console.error('Error fetching data', error);
      }
    };
    fetchData();
  }, [filters]);

  // Prepare trend data (group by week)
  const trendData = tableData.reduce((acc: any[], row: any) => {
    const week = row.week_ending?.split('T')[0] || 'Unknown';
    const existing = acc.find((d: any) => d.week === week);
    if (existing) {
      existing.hts_pct = (existing.hts_pct + (row.hts_mohcc_pct || 0)) / 2;
    } else {
      acc.push({ week, hts_pct: row.hts_mohcc_pct || 0 });
    }
    return acc;
  }, []);

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
            <QualitativeInsights
              insights={insights}
              aggregated={aggregatedInsights}
              totalFacilities={aggregated?.total_facilities}
            />
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <TrendChart
            data={trendData}
            xKey="week"
            yKeys={[{ key: 'hts_pct', color: '#8884d8', name: 'HTS MOHCC %' }]}
            title="HTS MOHCC Percentage Trend"
          />
        </Grid>
        <Grid item xs={12}>
          <DataTable data={tableData.slice(0, 20)} title="Facility Data (Top 20)" />
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;