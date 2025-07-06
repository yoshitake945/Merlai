import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Container from '@mui/material/Container';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import HomeIcon from '@mui/icons-material/Home';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

const SIDEBAR_WIDTH = 240;
const SIDEBAR_COLLAPSED_WIDTH = 60;

function Home({ handleCompose, result }) {
  return (
    <Container maxWidth="sm" sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', p: 0 }}>
      <Paper elevation={3} sx={{ width: '100%', p: { xs: 2, sm: 4 }, mt: 4 }}>
        <Typography variant="h4" align="center" gutterBottom>
          AI Composer
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2, justifyContent: 'center', alignItems: 'center', mb: 3 }}>
          <Button variant="contained" color="primary" onClick={handleCompose} sx={{ flex: 1 }}>
            Compose with AI
          </Button>
        </Box>
        <Box sx={{ minHeight: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#f5f5f5', borderRadius: 1, p: 2 }}>
          <Typography variant="subtitle1">
            <strong>Result:</strong> {result}
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}

function TimelineTracks() {
  // トラック定義
  const tracks = [
    { name: 'Vocal' },
    { name: 'Piano' },
    { name: 'Bass' },
    { name: 'Drums' },
  ];
  // ダミーの時間軸（16小節）
  const measures = Array.from({ length: 16 }, (_, i) => i + 1);

  // ダミーMIDIデータ: 各トラックごとに小節番号の配列でノート区間を定義
  const midiData = {
    Vocal: [3, 4, 5, 6],
    Piano: [2, 3, 4, 8, 9, 10],
    Bass: [5, 6, 7],
    Drums: [1, 2, 12, 13, 14],
  };

  // 色分け
  const trackColors = {
    Vocal: '#ffd54f',
    Piano: '#81d4fa',
    Bass: '#a5d6a7',
    Drums: '#ef9a9a',
  };

  return (
    <Box sx={{ width: '100%', overflowX: 'auto', bgcolor: '#f5f5f5', borderRadius: 2, p: 2 }}>
      {/* 時間軸 */}
      <Box sx={{ display: 'flex', mb: 1 }}>
        <Box sx={{ width: 80 }} />
        {measures.map((m) => (
          <Box key={m} sx={{ width: 64, textAlign: 'center', color: '#888', fontSize: 12 }}>
            {m}
          </Box>
        ))}
      </Box>
      {/* トラック行 */}
      {tracks.map((track) => (
        <Box key={track.name} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          {/* トラック名 */}
          <Paper sx={{ width: 80, mr: 1, p: 1, textAlign: 'center', bgcolor: '#e0f7fa', fontWeight: 600 }}>
            {track.name}
          </Paper>
          {/* トラックタイムライン */}
          <Box sx={{ display: 'flex', flex: 1 }}>
            {measures.map((m) => {
              const hasNote = midiData[track.name]?.includes(m);
              return (
                <Box
                  key={m}
                  sx={{
                    width: 64,
                    height: 32,
                    border: '1px solid #e0e0e0',
                    bgcolor: hasNote ? trackColors[track.name] : '#fff',
                    transition: 'background 0.2s',
                  }}
                />
              );
            })}
          </Box>
        </Box>
      ))}
    </Box>
  );
}

function App() {
  const [result, setResult] = useState('');
  // サイドバーの折りたたみ状態
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const handleSidebarToggle = () => setSidebarCollapsed((prev) => !prev);

  const handleCompose = () => {
    setResult('AI composed a song!');
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
          {/* AppBar */}
          <AppBar position="fixed" color="inherit" elevation={0} sx={{ borderBottom: '1px solid #e0e0e0', zIndex: 1201 }}>
            <Toolbar>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                Merlai
              </Typography>
            </Toolbar>
          </AppBar>
          {/* サイドバー＋メイン */}
          <Box sx={{ display: 'flex', pt: '64px', minHeight: '100vh' }}>
            {/* サイドバー */}
            <Paper
              elevation={1}
              sx={{
                width: sidebarCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
                transition: 'width 0.2s',
                height: 'calc(100vh - 64px)',
                position: 'fixed',
                top: 64,
                left: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                bgcolor: 'background.paper',
                borderRight: '1px solid #e0e0e0',
                zIndex: 1200,
                p: 0,
              }}
            >
              <Box sx={{ flex: 1, width: '100%', mt: 2 }}>
                <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1, borderRadius: 2, cursor: 'pointer', gap: 1, ':hover': { bgcolor: '#f5f5f5' } }}>
                    <HomeIcon fontSize="medium" />
                    {!sidebarCollapsed && (
                      <Typography variant="body1" sx={{ ml: 1 }}>
                        Home
                      </Typography>
                    )}
                  </Box>
                </Link>
                {/* 今後メニュー追加可 */}
              </Box>
              <Box sx={{ mb: 2 }}>
                <IconButton onClick={handleSidebarToggle} size="small">
                  {sidebarCollapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                </IconButton>
              </Box>
            </Paper>
            {/* メインコンテンツ */}
            <Box sx={{ flex: 1, ml: sidebarCollapsed ? `${SIDEBAR_COLLAPSED_WIDTH}px` : `${SIDEBAR_WIDTH}px`, transition: 'margin-left 0.2s', p: { xs: 1, sm: 3 } }}>
              {/* DAWタイムライン＋トラックレイアウト */}
              <TimelineTracks />
              {/* 今後: Home画面や他画面も追加可 */}
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
