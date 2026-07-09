import React, { useEffect, useState } from 'react';
import { Paper, Grid, TextField, Button, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { Filters as FiltersType } from '../types';
import { getProvinces, getDistricts } from '../api/client';

interface Props {
  onFilterChange: (filters: FiltersType) => void;
}

const Filters: React.FC<Props> = ({ onFilterChange }) => {
  const [provinces, setProvinces] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [selectedProvince, setSelectedProvince] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Load provinces on mount
  useEffect(() => {
    getProvinces().then(res => setProvinces(res.data));
  }, []);

  // Load districts when province changes
  useEffect(() => {
    if (selectedProvince) {
      getDistricts(selectedProvince).then(res => setDistricts(res.data));
    } else {
      getDistricts().then(res => setDistricts(res.data));
    }
    setSelectedDistrict(''); // reset district when province changes
  }, [selectedProvince]);

  const applyFilters = () => {
    onFilterChange({
      province: selectedProvince || undefined,
      district: selectedDistrict || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth>
            <InputLabel id="province-label">Province</InputLabel>
            <Select
              labelId="province-label"
              value={selectedProvince}
              label="Province"
              onChange={(e) => setSelectedProvince(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {provinces.map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={3}>
          <FormControl fullWidth>
            <InputLabel id="district-label">District</InputLabel>
            <Select
              labelId="district-label"
              value={selectedDistrict}
              label="District"
              onChange={(e) => setSelectedDistrict(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {districts.map(d => <MenuItem key={d} value={d}>{d}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <TextField
            fullWidth
            label="Start Date"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={2}>
          <TextField
            fullWidth
            label="End Date"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={2}>
          <Button fullWidth variant="contained" onClick={applyFilters}>
            Apply Filters
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default Filters;