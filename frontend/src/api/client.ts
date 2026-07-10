import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
});

export const getAggregatedData = (filters: any) =>
  api.get('/data/aggregated', { params: filters });

export const getTableData = (filters: any) =>
  api.get('/data/table', { params: filters });

export const getInsights = (filters: any) =>
  api.get('/insights', { params: filters });

export const getProvinces = () => 
  api.get('/filters/provinces');

export const getDistricts = (province?: string) => 
  api.get('/filters/districts', { params: { province } });
