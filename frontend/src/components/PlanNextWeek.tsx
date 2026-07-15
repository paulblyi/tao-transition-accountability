import React, {useState, useEffect} from 'react';
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

const PlanNextWeek: React.FC<{ data: any[]; summary: any }> = ({ data, summary }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    setPage(0);
  }, [data]);

  if (!data || data.length === 0) return <Typography>No plan data.</Typography>;

  const startIndex = page * rowsPerPage;
  const paginatedData = data.slice(startIndex, startIndex + rowsPerPage);
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>Plan for Next Week</Typography>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Facility</TableCell>
              <TableCell>Planned Activities</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{row.facility}</TableCell>
                <TableCell>{row.plan || '-'}</TableCell>
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