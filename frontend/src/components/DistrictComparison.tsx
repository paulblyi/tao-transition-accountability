import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Paper, Typography } from '@mui/material';

interface Props {
  data: any[];
}

const DistrictComparison: React.FC<Props> = ({ data }) => {
  // Aggregate by district
  const districtData = data.reduce((acc: any, row: any) => {
    const existing = acc.find((d: any) => d.district === row.district);
    if (existing) {
      existing.hts_avg = (existing.hts_avg + (row.hts_mohcc_pct || 0)) / 2;
    } else {
      acc.push({ district: row.district, hts_avg: row.hts_mohcc_pct || 0 });
    }
    return acc;
  }, []);

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>District Performance Comparison</Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={districtData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="district" />
          <YAxis label={{ value: 'HTS MOHCC %', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="hts_avg" fill="#006400" name="Avg HTS MOHCC %" />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
};