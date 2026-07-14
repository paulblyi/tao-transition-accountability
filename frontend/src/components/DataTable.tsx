import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
} from '@mui/material';

interface DataTableProps {
  data: any[];
  title?: string;
}

// Format any ISO date string to dd-MM-yyyy
const formatDate = (value: any): string => {
  // If it's a string that looks like an ISO date (starts with YYYY-MM-DDThh:mm:ss)
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}-${month}-${year}`;
    }
  }
  // If it's already a Date object (unlikely from API, but handle)
  if (value instanceof Date) {
    const day = String(value.getDate()).padStart(2, '0');
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const year = value.getFullYear();
    return `${day}-${month}-${year}`;
  }
  // Otherwise return the value unchanged
  return value;
};

const DataTable: React.FC<DataTableProps> = ({ data, title }) => {
  if (!data || data.length === 0) {
    return <Typography>No data available for the table.</Typography>;
  }

  const columns = Object.keys(data[0]);

  return (
    <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
      {title && (
        <Typography variant="h6" sx={{ p: 2 }}>
          {title}
        </Typography>
      )}
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
          {data.map((row, idx) => (
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
  );
};

export default DataTable;