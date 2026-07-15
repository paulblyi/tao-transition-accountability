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
  TablePagination,
} from '@mui/material';

const CapacityBuilding: React.FC<{ data: any[]; summary: any }> = ({ data, summary }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    setPage(0);
  }, [data]);

  if (!data || data.length === 0) return <Typography>No capacity data.</Typography>;

  const startIndex = page * rowsPerPage;
  const paginatedData = data.slice(startIndex, startIndex + rowsPerPage);

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" gutterBottom>Capacity Building & Workforce Transition</Typography>

      {summary && summary.summary && (
        <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 1, mb: 2 }}>
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
      )}

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Facility</TableCell>
              <TableCell>Gaps Supported</TableCell>
              <TableCell>Testers</TableCell>
              <TableCell>VIAC Trained</TableCell>
              <TableCell>VL Mentored</TableCell>
              <TableCell>AHD Supported</TableCell>
              <TableCell>Logistics</TableCell>
              <TableCell>OI Focal</TableCell>
              <TableCell>VHW Mentored</TableCell>
              <TableCell>Defaulter %</TableCell>
              <TableCell>Disruptions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((row, idx) => (
              <TableRow key={idx}>
                <TableCell>{row.facility}</TableCell>
                <TableCell>{row.gaps_supported || '-'}</TableCell>
                <TableCell>{row.nurse_testers || '-'}</TableCell>
                <TableCell>{row.viac_trained || '-'}</TableCell>
                <TableCell>{row.vl_mentored || '-'}</TableCell>
                <TableCell>{row.ahd_supported || '-'}</TableCell>
                <TableCell>{row.logistics_supported || '-'}</TableCell>
                <TableCell>{row.oi_focal || '-'}</TableCell>
                <TableCell>{row.vhw_mentored || '-'}</TableCell>
                <TableCell>{row.defaulter_pct || '-'}</TableCell>
                <TableCell>{row.disruptions || '-'}</TableCell>
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
    </Paper>
  );
};

export default CapacityBuilding;