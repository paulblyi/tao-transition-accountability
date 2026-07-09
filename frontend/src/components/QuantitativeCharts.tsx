import React from 'react';
import { Typography } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const QuantitativeCharts: React.FC<{ data: any }> = ({ data }) => {
  // Placeholder – you can create actual charts from aggregated data
  const chartData = [
    { name: 'HTS', MOHCC: data?.avg_hts_mohcc_pct || 0 },
    { name: 'VL', MOHCC: data?.avg_vl_mohcc_pct || 0 },
  ];
  return (
    <div>
      <Typography variant="h6" gutterBottom>Key Indicators</Typography>
      <BarChart width={400} height={250} data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="MOHCC" fill="#8884d8" />
      </BarChart>
    </div>
  );
};

export default QuantitativeCharts;
