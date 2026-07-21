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
  const [analysisMode, setAnalysisMode] = useState<string>('sample');

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
      analysis_mode: analysisMode,
    });
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Grid container spacing={2} alignItems="center">
        {/* Province */}
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

        {/* District */}
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

        {/* Start Date */}
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

        {/* End Date */}
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

        {/* AI Insights Toggle */}
        <Grid item xs={12} sm={1}>
          <FormControlLabel
            control={
              <Switch
                checked={useAI}
                onChange={(e) => onToggleAI(e.target.checked)}
                color="primary"
                size="small"
              />
            }
            label="AI"
            sx={{
              '& .MuiFormControlLabel-label': { fontSize: '0.875rem', fontWeight: 500 }
            }}
          />
        </Grid>

        {/* Analysis Mode Dropdown - disabled when AI is off */}
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth size="small" disabled={!useAI}>
            <InputLabel id="analysis-mode-label">Analysis Mode</InputLabel>
            <Select
              labelId="analysis-mode-label"
              value={analysisMode}
              label="Analysis Mode"
              onChange={(e) => setAnalysisMode(e.target.value)}
            >
              <MenuItem value="fallback">📊 Data Summary</MenuItem>
              <MenuItem value="sample">📝 Sample Insights</MenuItem>
              <MenuItem value="keyword">🔑 Keyword+Sample</MenuItem>
              <MenuItem value="chunked">🧩 Chunked Analysis</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        {/* Apply Button */}
        <Grid item xs={12} sm={1}>
          <Button fullWidth variant="contained" onClick={handleApply} size="small">
            Apply
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default Filters;