import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Box, CircularProgress, Typography } from '@mui/material';
import Filters from './Filters';
import ActiveFilters from './ActiveFilters';
import SummaryCards from './SummaryCards';
import QuantitativeCharts from './QuantitativeCharts';
import QualitativeInsights from './QualitativeInsights';
import { getAggregatedData, getInsights, getTableData } from '../api/client';
import { Filters as FiltersType, AggregatedData, Insight } from '../types';
import DataTable from './DataTable';
import TrendChart from './TrendChart';
import Header from './Header';
import GovernanceInsights from './GovernanceInsights';
import CategoricalSummary from './CategoricalSummary';
import ReportSections from './ReportSections';
import DistrictComparison from './DistrictComparison';
import FacilityScorecard from './FacilityScorecard';
import TransitionDashboard from './TransitionDashboard';

type AggregatedInsight = Insight & {
  facilities?: string;
  total_facilities?: number;
};

const Dashboard: React.FC = () => {
  const [filters, setFilters] = useState<FiltersType>({});
  const [appliedFilters, setAppliedFilters] = useState<FiltersType>({});
  const [filtersApplied, setFiltersApplied] = useState<boolean>(false);
  const [aggregated, setAggregated] = useState<AggregatedData | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [aggregatedInsights, setAggregatedInsights] = useState<AggregatedInsight | undefined>(undefined);
  const [tableData, setTableData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleFilterChange = (newFilters: FiltersType) => {
    setFilters(newFilters);
    setAppliedFilters(newFilters);
    setFiltersApplied(true);
  };

  useEffect(() => {
    if (!filtersApplied) return;
    const fetchData = async () => {
      setLoading(true);
      try {
        const [aggRes, insRes, tableRes] = await Promise.all([
          getAggregatedData(appliedFilters),
          getInsights(appliedFilters),
          getTableData(appliedFilters),
        ]);
        setAggregated(aggRes.data);
        setInsights(insRes.data.insights || []);
        setAggregatedInsights(insRes.data.aggregated || undefined);
        setTableData(tableRes.data || []);
      } catch (error) {
        console.error('Error fetching data', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [appliedFilters, filtersApplied]);

  // Prepare trend data – group by week
  const trendData = tableData.reduce((acc: any[], row: any) => {
    const week = row.week_ending?.split('T')[0] || 'Unknown';
    const existing = acc.find((d: any) => d.week === week);
    const avg = (current: number, newVal: number) => 
      current !== undefined ? (current + (newVal || 0)) / 2 : (newVal || 0);
    if (existing) {
      existing.hts_pct = avg(existing.hts_pct, row.hts_mohcc_pct);
      existing.vl_pct   = avg(existing.vl_pct, row.vl_mohcc_pct);
      existing.prep_pct = avg(existing.prep_pct, row.prep_mohcc_pct);
    } else {
      acc.push({ week, hts_pct: row.hts_mohcc_pct || 0, vl_pct: row.vl_mohcc_pct || 0, prep_pct: row.prep_mohcc_pct || 0 });
    }
    return acc;
  }, []);

  // SORT BY DATE (oldest to newest)
  trendData.sort((a, b) => new Date(a.week).getTime() - new Date(b.week).getTime());

  const renderContent = () => {
    if (!filtersApplied) {
      return (
        <Box sx={{ textAlign: 'center', my: 10 }}>
          <Typography variant="h5" color="textSecondary" gutterBottom>
            🔍 Apply Filters to Load Data
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Select a Province, District, or date range and click <strong>Apply Filters</strong> to view the dashboard.
          </Typography>
        </Box>
      );
    }

    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress size={60} />
        </Box>
      );
    }

    if (!aggregated || aggregated.total_facilities === 0) {
      return (
        <Box sx={{ textAlign: 'center', my: 10 }}>
          <Typography variant="h5" color="textSecondary" gutterBottom>
            No Data Found
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Try adjusting your filters or check that data exists.
          </Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={3}>
        {/* Row 1: Summary Cards */}
        <Grid item xs={12}>
          <SummaryCards data={aggregated} />
        </Grid>

        {/* Row 2: Categorical Summary */}
        <Grid item xs={12}>
          <CategoricalSummary filters={appliedFilters} />
        </Grid>

        {/* Row 3: Governance Insights */}
        <Grid item xs={12}>
          <GovernanceInsights filters={appliedFilters} />
        </Grid>

        {/* Row 4: Transition Dashboard */}
        <Grid item xs={12}>
          <TransitionDashboard filters={appliedFilters} />
        </Grid>

        {/* Rows 5-7: Left column (1/3) with three charts, Right column (2/3) with Qualitative Insights spanning all three */}
        <Grid item xs={12}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Grid container direction="column" spacing={3}>
                <Grid item>
                  <Paper sx={{ p: 2 }}>
                    <QuantitativeCharts data={aggregated} />
                  </Paper>
                </Grid>
                <Grid item>
                  <DistrictComparison data={tableData} />
                </Grid>
                <Grid item>
                  <FacilityScorecard data={tableData} maxItems={6} />
                </Grid>
              </Grid>
            </Grid>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <QualitativeInsights
                  insights={insights}
                  aggregated={aggregatedInsights}
                  totalFacilities={aggregated?.total_facilities}
                />
              </Paper>
            </Grid>
          </Grid>
        </Grid>

        {/* Row 8: Report Sections */}
        <Grid item xs={12}>
          <ReportSections filters={appliedFilters} />
        </Grid>

        {/* Row 9: Trend Chart – now sorted by date */}
        <Grid item xs={12}>
          <TrendChart
            data={trendData}
            xKey="week"
            yKeys={[
              { key: 'hts_pct', color: '#006400', name: 'HTS MOHCC %' },
              { key: 'vl_pct', color: '#FFD700', name: 'VL MOHCC %' },
              { key: 'prep_pct', color: '#D32F2F', name: 'PrEP MOHCC %' },
            ]}
            title="Weekly Performance Trends"
          />
        </Grid>

        {/* Row 10: Data Table */}
        <Grid item xs={12}>
          <DataTable data={tableData.slice(0, 20)} title="Facility Data (Top 20)" />
        </Grid>
      </Grid>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      <Header />
      <Filters onFilterChange={handleFilterChange} />
      <ActiveFilters filters={appliedFilters} />
      {renderContent()}
    </Container>
  );
};

export default Dashboard;