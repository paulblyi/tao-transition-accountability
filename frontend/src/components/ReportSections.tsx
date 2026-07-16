import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { getReportSections } from '../api/client';
import CapacityBuilding from './CapacityBuilding';
import FinancialSustainability from './FinancialSustainability';
import ChallengesMitigations from './ChallengesMitigations';
import PlanNextWeek from './PlanNextWeek';

interface Props {
  filters: any;
  enabled: boolean;
}

const ReportSections: React.FC<Props> = ({ filters, enabled }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getReportSections(filters, !enabled); // skip_llm = NOT enabled
        setData(res.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load report sections');
        console.error('Report sections error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filters, enabled]);

  if (!enabled) {
    // Show tables anyway with rule-based summaries (they are included in the response)
    if (loading) return <CircularProgress />;
    if (error) return <Alert severity="error">{error}</Alert>;
    if (!data) return <Typography>No data available.</Typography>;

    return (
      <>
        <CapacityBuilding data={data.capacity} summary={data.summaries?.capacity} />
        <FinancialSustainability data={data.financial} summary={data.summaries?.financial} />
        <ChallengesMitigations data={data.challenges} summary={data.summaries?.challenges} />
        <PlanNextWeek data={data.plans} summary={data.summaries?.plans} />
      </>
    );
  }

  // AI enabled – still show tables and summaries (they may be LLM or fallback)
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress size={30} />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!data) {
    return <Typography>No data available for the selected filters.</Typography>;
  }

  return (
    <>
      <CapacityBuilding data={data.capacity} summary={data.summaries?.capacity} />
      <FinancialSustainability data={data.financial} summary={data.summaries?.financial} />
      <ChallengesMitigations data={data.challenges} summary={data.summaries?.challenges} />
      <PlanNextWeek data={data.plans} summary={data.summaries?.plans} />
    </>
  );
};

export default ReportSections;