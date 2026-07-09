import React from 'react';
import { Typography, List, ListItem, ListItemText, Divider, Chip, Box } from '@mui/material';
import { Insight } from '../types';

interface Props {
  insights: Insight[];
}

const QualitativeInsights: React.FC<Props> = ({ insights }) => {
  if (!insights || insights.length === 0) {
    return <Typography>No qualitative insights available.</Typography>;
  }

  // Aggregate category frequencies
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

  // Collect all challenges and mitigations (flatten)
  const allChallenges = insights.flatMap(ins => ins.challenges || []);
  const allMitigations = insights.flatMap(ins => ins.mitigations || []);

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        AI Generated Insights
      </Typography>

      {topCategories.length > 0 && (
        <>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Top Themes:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
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
        Sample Summaries:
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
