import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';

const Header: React.FC = () => {
  return (
    <AppBar 
      position="static" 
      sx={{ 
        background: 'linear-gradient(135deg, #006400 0%, #006400 30%, #FFD700 50%, #FFD700 70%, #006400 100%)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        mb: 3
      }}
    >
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          {/* ZHI Logo – raised by shifting it up */}
          <img 
            src="/zhi_logo.png" 
            alt="ZHI Logo" 
            style={{ 
              height: '55px', 
              width: 'auto', 
              marginTop: '-6px',     // pulls the logo upward
              objectFit: 'contain' 
            }} 
          />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'white', textShadow: '1px 1px 3px rgba(0,0,0,0.3)' }}>
              TAO Transition Accountability System
            </Typography>
            <Typography variant="subtitle1" sx={{ color: 'rgba(255,255,255,0.9)' }}>
              Zimbabwe - HIV Programme Transition Monitoring
            </Typography>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;