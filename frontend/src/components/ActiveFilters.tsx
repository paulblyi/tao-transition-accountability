import React from 'react';
import { Paper, Chip, Box, Typography } from '@mui/material';

interface Props {
  filters: any;
}

const ActiveFilters: React.FC<Props> = ({ filters }) => {
  const { province, district, start_date, end_date } = filters;
  const hasFilters = province || district || start_date || end_date;
  
  if (!hasFilters) {
    return (
      <Paper sx={{ p: 1, mb: 2, bgcolor: '#f5f5f5' }}>
        <Typography variant="body2" color="textSecondary">No filters applied – showing all data.</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 1, mb: 2, bgcolor: '#f5f5f5' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Active Filters:</Typography>
        {province && <Chip label={`Province: ${province}`} size="small" />}
        {district && <Chip label={`District: ${district}`} size="small" />}
        {start_date && <Chip label={`From: ${start_date}`} size="small" />}
        {end_date && <Chip label={`To: ${end_date}`} size="small" />}
      </Box>
    </Paper>
  );
};

export default ActiveFilters;