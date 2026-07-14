import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#006400', // Zimbabwe green
      light: '#228B22',
      dark: '#004d00',
    },
    secondary: {
      main: '#FFD700', // Zimbabwe gold
      light: '#FFEB3B',
      dark: '#F9A825',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    warning: {
      main: '#D32F2F', // Zimbabwe red (accent)
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderLeft: '4px solid #006400',
          borderRadius: '8px',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
        },
      },
    },
  },
});

export default theme;