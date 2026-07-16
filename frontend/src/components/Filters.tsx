import React, { useState, useEffect } from 'react';
import {
  Paper, Grid, TextField, Button, Select, MenuItem,
  FormControl, InputLabel, Switch, FormControlLabel, Box
} from '@mui/material';
import { Filters as FiltersType } from '../types';
import { getProvinces, getDistricts } from '../api/client';

interface Props {
  onFilterChange: (filters: FiltersType) => void;
  useAI: boolean;
  onToggleAI: (value: boolean) => void;
}

const Filters: React.FC<Props> = ({ onFilterChange, useAI, onToggleAI }) => {
  const [provinces, setProvinces] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [selectedProvince, setSelectedProvince] = useState<string>('all');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    getProvinces().then(res => setProvinces(res.data));
  }, []);

  useEffect(() => {
    if (selectedProvince && selectedProvince !== 'all') {
      getDistricts(selectedProvince).then(res => setDistricts(res.data));
    } else {
      getDistricts().then(res => setDistricts(res.data));
    }
    setSelectedDistrict('all');
  }, [selectedProvince]);

  const handleApply = () => {
    onFilterChange({
      province: selectedProvince === 'all' ? undefined : selectedProvince,
      district: selectedDistrict === 'all' ? undefined : selectedDistrict,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth size="small">
            <InputLabel id="province-label">Province</InputLabel>
            <Select
              labelId="province-label"
              value={selectedProvince}
              label="Province"
              onChange={(e) => setSelectedProvince(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              {provinces.map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth size="small">
            <InputLabel id="district-label">District</InputLabel>
            <Select
              labelId="district-label"
              value={selectedDistrict}
              label="District"
              onChange={(e) => setSelectedDistrict(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              {districts.map(d => <MenuItem key={d} value={d}>{d}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <TextField
            fullWidth
            label="Start Date"
            type="date"
            size="small"
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
            size="small"
            InputLabelProps={{ shrink: true }}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </Grid>

        {/* AI Toggle + Apply Button */}
        <Grid item xs={12} sm={4}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={useAI}
                  onChange={(e) => onToggleAI(e.target.checked)}
                  color="primary"
                  size="small"
                />
              }
              label="AI Insights"
              sx={{ 
                mr: 1,
                '& .MuiFormControlLabel-label': { fontSize: '0.875rem', fontWeight: 500 }
              }}
            />
            <Button variant="contained" onClick={handleApply} size="small">
              Apply
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default Filters;