import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#AEEA00', // 明るい黄緑
      contrastText: '#222',
    },
    secondary: {
      main: '#B2FF59', // さらに淡い黄緑
      contrastText: '#222',
    },
    background: {
      default: '#f9fbe7', // ごく薄い黄緑系
      paper: '#ffffff',
    },
  },
  shape: {
    borderRadius: 12, // 角丸をやや大きめに
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: 'none', // 影をなくしてフラットに
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // ボタンの大文字化をやめる
          fontWeight: 600,
        },
      },
    },
  },
});

export default theme; 