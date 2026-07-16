import axios from 'axios';

const api = axios.create({
  // baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  baseURL: process.env.REACT_APP_API_URL || '/api',

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

export const getCategoricalSummary = (filters: any) =>
  api.get('/categorical/summary', { params: filters });

export const getCoverage = (filters: any) =>
  api.get('/coverage/district', { params: filters });

export const getTransitionRisk = (filters: any) =>
  api.get('/coverage/risk', { params: filters });

export const getGovernanceInsights = (filters: any, skip_llm: boolean = false) =>
  api.get('/categorical/insights', { params: { ...filters, skip_llm } });

export const getReportSections = (filters: any, skip_llm: boolean = false) =>
  api.get('/report/sections', { params: { ...filters, skip_llm } });

export const getRiskNarrative = (filters: any, skip_llm: boolean = false) =>
  api.get('/coverage/narrative', { params: { ...filters, skip_llm } });