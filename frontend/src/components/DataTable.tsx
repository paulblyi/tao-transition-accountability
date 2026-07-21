import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  TablePagination,
  Box,
  Card,
  CardContent,
} from '@mui/material';

interface DataTableProps {
  data: any[];
  title?: string;
}

// Format ISO date to dd-MM-yyyy
const formatDate = (value: any): string => {
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}-${month}-${year}`;
    }
  }
  if (value instanceof Date) {
    const day = String(value.getDate()).padStart(2, '0');
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const year = value.getFullYear();   // <-- FIXED: use 'value' not 'date'
    return `${day}-${month}-${year}`;
  }
  return value;
};

// Check if a column is a percentage column (contains 'pct' or 'percentage')
const isPercentageColumn = (key: string): boolean => {
  return key.toLowerCase().includes('pct') || key.toLowerCase().includes('percentage');
};

// Calculate summary statistics for a column
const calculateStats = (data: any[], columnKey: string) => {
  const values = data
    .map(row => parseFloat(row[columnKey]))
    .filter(val => !isNaN(val) && val !== null && val !== undefined);

  if (values.length === 0) return null;

  const sum = values.reduce((a, b) => a + b, 0);
  const avg = sum / values.length;
  const min = Math.min(...values);
  const max = Math.max(...values);

  return { avg, min, max };
};

const DataTable: React.FC<DataTableProps> = ({ data, title = "Facility Data" }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    setPage(0);
  }, [data]);

  if (!data || data.length === 0) {
    return <Typography>No data available for the table.</Typography>;
  }

  const columns = Object.keys(data[0]);
  const startIndex = page * rowsPerPage;
  const paginatedData = data.slice(startIndex, startIndex + rowsPerPage);

  // Compute stats for percentage columns (using full dataset)
  const pctColumns = columns.filter(isPercentageColumn);
  const stats: Record<string, { avg: number; min: number; max: number } | null> = {};
  pctColumns.forEach(col => {
    stats[col] = calculateStats(data, col);
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>{title}</Typography>

      {/* Summary Statistics – beautified as a single row of cards */}
      {pctColumns.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            📊 Summary Statistics (based on {data.length} facilities)
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1.5,
              justifyContent: 'flex-start',
            }}
          >
            {pctColumns.map((col) => {
              const s = stats[col];
              if (!s) return null;
              return (
                <Card
                  key={col}
                  variant="outlined"
                  sx={{
                    minWidth: 120,
                    flex: '1 1 auto',
                    maxWidth: 200,
                    bgcolor: '#fafafa',
                  }}
                >
                  <CardContent sx={{ py: 1, px: 1.5 }}>
                    <Typography variant="caption" color="textSecondary" sx={{ fontWeight: 'bold' }}>
                      {col.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="body2">
                        <strong>Avg:</strong> {s.avg.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        <strong>Min:</strong> {s.min.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        <strong>Max:</strong> {s.max.toFixed(1)}%
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              );
            })}
          </Box>
        </Box>
      )}

      {/* Table */}
      <TableContainer>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col} sx={{ fontWeight: 'bold' }}>
                  {col.replace(/_/g, ' ').toUpperCase()}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((row, idx) => (
              <TableRow key={idx}>
                {columns.map((col) => (
                  <TableCell key={col}>
                    {formatDate(row[col])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
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

export default DataTable;