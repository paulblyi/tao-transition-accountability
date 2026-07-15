import React from 'react';
import { Box, Typography } from '@mui/material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        background: 'linear-gradient(135deg, #006400 0%, #006400 30%, #FFD700 50%, #FFD700 70%, #006400 100%)',
        boxShadow: '0 -4px 20px rgba(0,0,0,0.1)',
        py: 1.5,   // thinner than header (header had py: 2)
        px: 3,
        mt: 4,
        textAlign: 'center',
        width: '100%',
      }}
    >
      <Typography
        variant="body2"
        sx={{
          color: 'white',
          textShadow: '1px 1px 3px rgba(0,0,0,0.3)',
          fontWeight: 'bold',
          letterSpacing: '0.5px',
        }}
      >
        Zimbabwe Health Interventions – Accelerated and Comprehensive HIV Care for Epidemic Control in Zimbabwe (ACCE) – {' '}
        <Box component="span" sx={{ display: 'inline-block' }}>© 2026</Box>
      </Typography>
    </Box>
  );
};

export default Footer;