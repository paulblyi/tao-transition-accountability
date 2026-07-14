import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import { getReportSections } from '../api/client';
import CapacityBuilding from './CapacityBuilding';
import FinancialSustainability from './FinancialSustainability';
import ChallengesMitigations from './ChallengesMitigations';
import PlanNextWeek from './PlanNextWeek';

const ReportSections: React.FC<{ filters: any }> = ({ filters }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getReportSections(filters);
        setData(res.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load report sections');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filters]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!data) return <Alert severity="info">No data available.</Alert>;

  return (
    <Box>
      <CapacityBuilding data={data.capacity} summary={data.summaries?.capacity} />
      <FinancialSustainability data={data.financial} summary={data.summaries?.financial} />
      <ChallengesMitigations data={data.challenges} summary={data.summaries?.challenges} />
      <PlanNextWeek data={data.plans} summary={data.summaries?.plans} />
    </Box>
  );
};

export default ReportSections;
