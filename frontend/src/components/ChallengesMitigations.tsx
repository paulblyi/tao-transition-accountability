import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Box, 
  Divider,
  TablePagination, 
} from '@mui/material';

const ChallengesMitigations: React.FC<{ data: any[]; summary: any }> = ({ data, summary }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    setPage(0);
  }, [data]);

  if (!data || data.length === 0) return <Typography>No challenges data.</Typography>;

  const startIndex = page * rowsPerPage;
  const paginatedData = data.slice(startIndex, startIndex + rowsPerPage);

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>Major Challenges & Mitigation Strategies</Typography>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Facility</TableCell>
              <TableCell>Challenges</TableCell>
              <TableCell>Mitigation Strategies</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{row.facility}</TableCell>
                <TableCell>{row.challenges || '-'}</TableCell>
                <TableCell>{row.mitigations || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={data.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(e, newPage) => setPage(newPage)}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10));
          setPage(0);
        }}
      />
      {/* Bottom Summary */}
      {summary && summary.summary && (
        <>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>📌 Key Takeaways</Typography>
            <Typography variant="body2" paragraph>{summary.summary}</Typography>
            {summary.common_challenges && summary.common_challenges.length > 0 && (
              <Typography variant="body2"><strong>Common Challenges:</strong> {summary.common_challenges.join(', ')}</Typography>
            )}
            {summary.effective_mitigations && summary.effective_mitigations.length > 0 && (
              <Typography variant="body2"><strong>Effective Mitigations:</strong> {summary.effective_mitigations.join(', ')}</Typography>
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
export default ChallengesMitigations;