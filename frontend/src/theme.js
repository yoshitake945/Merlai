import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#222831', // Dark gray
      contrastText: '#eeeeee',
    },
    secondary: {
      main: '#393e46', // Deeper gray
      contrastText: '#eeeeee',
    },
    background: {
      default: '#181920', // Almost black
      paper: '#23272f',   // Dark paper
    },
  },
  shape: {
    borderRadius: 12, // Slightly larger border radius
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: 'none', // Remove shadow for flat look
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // No uppercase for buttons
          fontWeight: 600,
        },
      },
    },
  },
});

export default theme; 