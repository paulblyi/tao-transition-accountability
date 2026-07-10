import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Typography, Paper } from '@mui/material';

interface TrendChartProps {
  data: any[];
  xKey: string;
  yKeys: { key: string; color: string; name: string }[];
  title?: string;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, xKey, yKeys, title }) => {
  if (!data || data.length === 0) {
    return <Typography>No trend data available.</Typography>;
  }

  return (
    <Paper sx={{ p: 2 }}>
      {title && <Typography variant="h6" gutterBottom>{title}</Typography>}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          {yKeys.map(({ key, color, name }) => (
            <Line key={key} type="monotone" dataKey={key} stroke={color} name={name} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
};

export default TrendChart;
