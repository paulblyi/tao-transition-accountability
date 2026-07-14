import React from 'react';
import { Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Divider } from '@mui/material';

const FinancialSustainability: React.FC<{ data: any[]; summary: any }> = ({ data, summary }) => {
  if (!data || data.length === 0) return <Typography>No financial data.</Typography>;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>Financial Sustainability & Resource Mobilization</Typography>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Facility</TableCell>
              <TableCell>Histology</TableCell>
              <TableCell>Histology Comment</TableCell>
              <TableCell>Airtime</TableCell>
              <TableCell>Airtime Comment</TableCell>
              <TableCell>Fuel</TableCell>
              <TableCell>Fuel Comment</TableCell>
              <TableCell>Stationery</TableCell>
              <TableCell>Stationery Comment</TableCell>
              <TableCell>CATS Stipends</TableCell>
              <TableCell>CATS Comment</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{row.facility}</TableCell>
                <TableCell>{row.histology || '-'}</TableCell>
                <TableCell>{row.histology_comment || '-'}</TableCell>
                <TableCell>{row.airtime || '-'}</TableCell>
                <TableCell>{row.airtime_comment || '-'}</TableCell>
                <TableCell>{row.fuel || '-'}</TableCell>
                <TableCell>{row.fuel_comment || '-'}</TableCell>
                <TableCell>{row.stationery || '-'}</TableCell>
                <TableCell>{row.stationery_comment || '-'}</TableCell>
                <TableCell>{row.cats_stipends || '-'}</TableCell>
                <TableCell>{row.cats_comment || '-'}</TableCell>
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
            {summary.strengths && summary.strengths.length > 0 && (
              <Typography variant="body2"><strong>Strengths:</strong> {summary.strengths.join(', ')}</Typography>
            )}
            {summary.gaps && summary.gaps.length > 0 && (
              <Typography variant="body2"><strong>Gaps:</strong> {summary.gaps.join(', ')}</Typography>
            )}
            {summary.recommendations && summary.recommendations.length > 0 && (
              <Typography variant="body2"><strong>Recommendations:</strong> {summary.recommendations.join(', ')}</Typography>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
};
export default FinancialSustainability;