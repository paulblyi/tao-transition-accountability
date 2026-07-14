import React from 'react';
import { Typography, List, ListItem, ListItemText, Divider, Chip, Box } from '@mui/material';
import { Insight } from '../types';

interface Props {
  insights: Insight[];
  aggregated?: Insight & { facilities?: string; total_facilities?: number };
  totalFacilities?: number;
}

const QualitativeInsights: React.FC<Props> = ({ insights, aggregated, totalFacilities }) => {
  if (!insights || insights.length === 0) {
    return <Typography>No qualitative insights available.</Typography>;
  }

  // Aggregate category frequencies from individual insights
  const categoryCounts: Record<string, number> = {};
  insights.forEach(ins => {
    ins.categories?.forEach(cat => {
      const key = cat.trim();
      categoryCounts[key] = (categoryCounts[key] || 0) + 1;
    });
  });
  const topCategories = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  // Collect all challenges and mitigations
  const allChallenges = insights.flatMap(ins => ins.challenges || []);
  const allMitigations = insights.flatMap(ins => ins.mitigations || []);

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Generated Insights
      </Typography>

      {aggregated && (
        <>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            📊 Aggregated Summary ({aggregated.total_facilities || totalFacilities || '?'} facilities)
          </Typography>
          <Typography variant="body2" paragraph sx={{ fontStyle: 'italic', bgcolor: '#f5f5f5', p: 1, borderRadius: 1 }}>
            {aggregated.summary}
          </Typography>
          <Divider sx={{ my: 1 }} />
        </>
      )}

      {topCategories.length > 0 && (
        <>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Top Themes:
          </Typography>
          {/* <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}> */}
          <Box sx={{ maxHeight: '500px', overflowY: 'auto' }}>
            {topCategories.map(([cat, count]) => (
              <Chip key={cat} label={`${cat} (${count})`} size="small" />
            ))}
          </Box>
        </>
      )}

      {allChallenges.length > 0 && (
        <>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Key Challenges:
          </Typography>
          <List dense sx={{ mb: 1 }}>
            {allChallenges.slice(0, 5).map((challenge, idx) => (
              <ListItem key={idx}>
                <ListItemText primary={`• ${challenge}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}

      {allMitigations.length > 0 && (
        <>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Suggested Mitigations:
          </Typography>
          <List dense>
            {allMitigations.slice(0, 5).map((mitigation, idx) => (
              <ListItem key={idx}>
                <ListItemText primary={`• ${mitigation}`} />
              </ListItem>
            ))}
          </List>
        </>
      )}

      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
        Sample Individual Summaries:
      </Typography>
      {insights.slice(0, 3).map((ins, idx) => (
        <Typography key={idx} variant="body2" paragraph sx={{ fontStyle: 'italic' }}>
          • {ins.summary}
        </Typography>
      ))}
    </div>
  );
};

export default QualitativeInsights;
