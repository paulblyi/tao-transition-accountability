import React from 'react';
import { Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Divider } from '@mui/material';

const PlanNextWeek: React.FC<{ data: any[]; summary: any }> = ({ data, summary }) => {
  if (!data || data.length === 0) return <Typography>No plan data.</Typography>;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>7. Plan for Next Week</Typography>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Facility</TableCell>
              <TableCell>Planned Activities</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{row.facility}</TableCell>
                <TableCell>{row.plan || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Bottom Summary */}
      {summary && summary.summary && (
        <>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>📌 Key Takeaways</Typography>
            <Typography variant="body2" paragraph>{summary.summary}</Typography>
            {summary.common_activities && summary.common_activities.length > 0 && (
              <Typography variant="body2"><strong>Common Activities:</strong> {summary.common_activities.join(', ')}</Typography>
            )}
            {summary.priority_areas && summary.priority_areas.length > 0 && (
              <Typography variant="body2"><strong>Priority Areas:</strong> {summary.priority_areas.join(', ')}</Typography>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
};
export default PlanNextWeek;