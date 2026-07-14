import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Paper, Typography } from '@mui/material';

interface Props {
  data: any[];
}

const DistrictComparison: React.FC<Props> = ({ data }) => {
  if (!data || data.length === 0) {
    return <Typography>No district data available.</Typography>;
  }

  // Aggregate by district
  const districtMap: Record<string, { total: number; count: number }> = {};
  data.forEach((row) => {
    if (!row.district) return;
    if (!districtMap[row.district]) {
      districtMap[row.district] = { total: 0, count: 0 };
    }
    districtMap[row.district].total += row.hts_mohcc_pct || 0;
    districtMap[row.district].count += 1;
  });

  const chartData = Object.entries(districtMap).map(([district, vals]) => ({
    district,
    avg_hts: vals.count > 0 ? Math.round((vals.total / vals.count) * 10) / 10 : 0,
  }));

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>District Performance Comparison</Typography>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="district" />
          <YAxis domain={[0, 100]} label={{ value: 'HTS MOHCC %', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="avg_hts" fill="#006400" name="Avg HTS MOHCC %" />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
};

export default DistrictComparison;