import { useState, useRef, useEffect } from 'react'
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
  const measures = Array.from({ length: 16 }, (_, i) => i + 1);
  const [midiData, setMidiData] = useState({
    Vocal: [ { start: 3, length: 2 }, { start: 6, length: 2 } ],
    Piano: [ { start: 2, length: 3 }, { start: 8, length: 2 } ],
    Bass:  [ { start: 5, length: 2 } ],
    Drums: [ { start: 1, length: 1 }, { start: 12, length: 2 } ],
  });
  const trackColors = {
    Vocal: '#ffd54f',
    Piano: '#81d4fa',
    Bass: '#a5d6a7',
    Drums: '#ef9a9a',
  };

  // 複数選択: [{track, noteIdx}]
  const [selectedNotes, setSelectedNotes] = useState([]); // Array<{track, noteIdx}>
  // ドラッグ状態
  const [dragInfo, setDragInfo] = useState(null); // {startX, originStarts, track, noteIdx}
  const timelineRef = useRef();

  // ドラッグ開始
  const handleDragStart = (e, track, noteIdx) => {
    e.stopPropagation();
    // 複数選択時は選択中すべて、単独時はそのノートのみ
    const isSelected = selectedNotes.some(sel => sel.track === track && sel.noteIdx === noteIdx);
    let movingNotes;
    if (isSelected) {
      movingNotes = selectedNotes;
    } else {
      movingNotes = [{ track, noteIdx }];
      setSelectedNotes([{ track, noteIdx }]);
    }
    // 各ノートの元のstart値
    const originStarts = movingNotes.map(sel => midiData[sel.track][sel.noteIdx].start);
    setDragInfo({
      startX: e.clientX,
      movingNotes,
      originStarts,
    });
    document.body.style.cursor = 'grabbing';
  };

  // ドラッグ中
  const handleDrag = (e) => {
    if (!dragInfo) return;
    const dx = e.clientX - dragInfo.startX;
    const delta = Math.round(dx / 64); // 1小節=64px
    if (delta === 0) return;
    setMidiData(prev => {
      const next = JSON.parse(JSON.stringify(prev));
      dragInfo.movingNotes.forEach((sel, i) => {
        const orig = dragInfo.originStarts[i];
        let newStart = orig + delta;
        newStart = Math.max(1, Math.min(16 - next[sel.track][sel.noteIdx].length + 1, newStart));
        next[sel.track][sel.noteIdx].start = newStart;
      });
      return next;
    });
  };

  // ドラッグ終了
  const handleDragEnd = () => {
    setDragInfo(null);
    document.body.style.cursor = '';
  };

  // グローバルイベント登録
  useEffect(() => {
    if (dragInfo) {
      window.addEventListener('mousemove', handleDrag);
      window.addEventListener('mouseup', handleDragEnd);
      return () => {
        window.removeEventListener('mousemove', handleDrag);
        window.removeEventListener('mouseup', handleDragEnd);
      };
    }
  }, [dragInfo]);

  return (
    <Box ref={timelineRef} sx={{ width: '100%', overflowX: 'auto', bgcolor: '#f5f5f5', borderRadius: 2, p: 2 }}>
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
          {/* トラック名（クリックで選択: いったん単一選択のまま） */}
          <Paper
            sx={{
              width: 80,
              mr: 1,
              p: 1,
              textAlign: 'center',
              bgcolor: '#e0f7fa',
              fontWeight: 600,
              cursor: 'pointer',
              border: 'none',
              transition: 'all 0.2s',
            }}
            onClick={() => {
              // トラック名クリック時はノート選択解除
              setSelectedNotes([]);
            }}
          >
            {track.name}
          </Paper>
          {/* トラックタイムライン */}
          <Box sx={{ display: 'flex', flex: 1, position: 'relative' }}>
            {/* 小節ごとに空セルを描画 */}
            {measures.map((m) => (
              <Box key={m} sx={{ width: 64, height: 32, border: '1px solid #e0e0e0', bgcolor: '#fff', position: 'relative', zIndex: 1 }} />
            ))}
            {/* ノートバーを重ねて描画（複数選択対応） */}
            {midiData[track.name]?.map((note, idx) => {
              const isSelected = selectedNotes.some(sel => sel.track === track.name && sel.noteIdx === idx);
              return (
                <Box
                  key={idx}
                  sx={{
                    position: 'absolute',
                    left: (note.start - 1) * 64,
                    width: note.length * 64 - 8,
                    height: 24,
                    top: 4,
                    bgcolor: isSelected ? '#fffde7' : trackColors[track.name],
                    borderRadius: 2,
                    zIndex: 2,
                    boxShadow: isSelected ? '0 0 0 2px #fbc02d' : '0 1px 4px #0002',
                    display: 'flex',
                    alignItems: 'center',
                    pl: 1,
                    fontWeight: 500,
                    fontSize: 14,
                    color: '#333',
                    overflow: 'hidden',
                    cursor: dragInfo ? 'grabbing' : 'pointer',
                    border: isSelected ? '2px solid #fbc02d' : 'none',
                    transition: 'all 0.2s',
                    opacity: dragInfo && isSelected ? 0.7 : 1,
                  }}
                  onClick={e => {
                    e.stopPropagation();
                    const isMeta = e.metaKey || e.ctrlKey;
                    if (isMeta) {
                      setSelectedNotes(prev => {
                        const exists = prev.some(sel => sel.track === track.name && sel.noteIdx === idx);
                        if (exists) {
                          return prev.filter(sel => !(sel.track === track.name && sel.noteIdx === idx));
                        } else {
                          return [...prev, { track: track.name, noteIdx: idx }];
                        }
                      });
                    } else {
                      setSelectedNotes([{ track: track.name, noteIdx: idx }]);
                    }
                  }}
                  onMouseDown={e => handleDragStart(e, track.name, idx)}
                >
                  {track.name} note
                </Box>
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
