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
  Chip,
  IconButton,
  Collapse,
  TablePagination,
  CircularProgress,
  Alert,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { getCategoricalSummary } from '../api/client';

interface CategoricalData {
  indicator: string;
  yes: number;
  no: number;
  unknown: number;
  total: number;
  yes_percentage: number;
  comments: { facility: string; comment: string }[];
  total_comments: number;
}

interface Props {
  filters: any;
}

const CategoricalSummary: React.FC<Props> = ({ filters }) => {
  const [data, setData] = useState<CategoricalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  // Reset page when data changes (e.g., new filters)
  useEffect(() => {
    setPage(0);
  }, [data]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getCategoricalSummary(filters);
        // Ensure data is an array (fallback to empty array)
        setData(Array.isArray(response.data) ? response.data : []);
      } catch (err: any) {
        setError(err.message || 'Failed to load categorical data');
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filters]);

  // Handlers
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0); // Reset to first page when rows per page changes
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Key Indicators Summary</Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress size={30} />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Key Indicators Summary</Typography>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Key Indicators Summary</Typography>
        <Typography variant="body2" color="textSecondary">
          No categorical data available for the selected filters.
        </Typography>
      </Paper>
    );
  }

  const toggleExpand = (indicator: string) => {
    setExpanded(expanded === indicator ? null : indicator);
  };

  // Slice data for current page
  const startIndex = page * rowsPerPage;
  const paginatedData = data.slice(startIndex, startIndex + rowsPerPage);

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Key Indicators Summary</Typography>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>Indicator</TableCell>
              <TableCell align="center" sx={{ fontWeight: 'bold' }}>Yes (%)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 'bold' }}>No</TableCell>
              <TableCell align="center" sx={{ fontWeight: 'bold' }}>Unknown</TableCell>
              <TableCell align="center" sx={{ fontWeight: 'bold' }}>Total</TableCell>
              <TableCell align="center" sx={{ fontWeight: 'bold' }}>Comments</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((row) => (
              <React.Fragment key={row.indicator}>
                <TableRow hover>
                  <TableCell>{row.indicator}</TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                      <Chip
                        label={`${row.yes}`}
                        size="small"
                        color={row.yes_percentage >= 80 ? 'success' : row.yes_percentage >= 50 ? 'warning' : 'error'}
                      />
                      <Typography variant="body2" color="textSecondary">
                        ({row.yes_percentage}%)
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">{row.no}</TableCell>
                  <TableCell align="center">{row.unknown}</TableCell>
                  <TableCell align="center">{row.total}</TableCell>
                  <TableCell align="center">
                    {row.total_comments > 0 && (
                      <IconButton size="small" onClick={() => toggleExpand(row.indicator)}>
                        <ExpandMoreIcon sx={{ transform: expanded === row.indicator ? 'rotate(180deg)' : 'rotate(0deg)' }} />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
                {row.total_comments > 0 && (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ py: 0 }}>
                      <Collapse in={expanded === row.indicator} timeout="auto" unmountOnExit>
                        <Box sx={{ py: 2, px: 2 }}>
                          <Typography variant="subtitle2" gutterBottom color="textSecondary">
                            Sample Comments (showing {row.comments.length} of {row.total_comments}):
                          </Typography>
                          {row.comments.map((c, idx) => (
                            <Typography key={idx} variant="body2" paragraph sx={{ fontStyle: 'italic', pl: 2 }}>
                              <strong>{c.facility}:</strong> {c.comment}
                            </Typography>
                          ))}
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
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
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
};

export default CategoricalSummary;