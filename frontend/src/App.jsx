import React from 'react';
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
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { v4 as uuidv4 } from 'uuid';

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
  // Track state
  const [tracks, setTracks] = useState([
    { name: 'Vocal' },
    { name: 'Piano' },
    { name: 'Bass' },
    { name: 'Drums' },
  ]);
  const [trackColors, setTrackColors] = useState({
    Vocal: '#00adb5',   // Vivid teal
    Piano: '#ffb300',   // Bright orange
    Bass:  '#7c4dff',   // Bright purple
    Drums: '#43a047',   // Vivid green
  });
  const [midiData, setMidiData] = useState({
    Vocal: [ { id: uuidv4(), start: 3, length: 2 }, { id: uuidv4(), start: 6, length: 2 } ],
    Piano: [ { id: uuidv4(), start: 2, length: 3 }, { id: uuidv4(), start: 8, length: 2 } ],
    Bass:  [ { id: uuidv4(), start: 5, length: 2 } ],
    Drums: [ { id: uuidv4(), start: 1, length: 1 }, { id: uuidv4(), start: 12, length: 2 } ],
  });
  const measures = Array.from({ length: 16 }, (_, i) => i + 1);
  // Track name width (resizable)
  const [trackNameWidth, setTrackNameWidth] = useState(120);
  const [resizing, setResizing] = useState(false);
  const resizeStartX = useRef(null);
  const resizeStartWidth = useRef(null);
  // Mouse events for resizing
  useEffect(() => {
    if (!resizing) return;
    const handleMouseMove = (e) => {
      const dx = e.clientX - resizeStartX.current;
      let newWidth = resizeStartWidth.current + dx;
      newWidth = Math.max(60, Math.min(300, newWidth));
      setTrackNameWidth(newWidth);
    };
    const handleMouseUp = () => setResizing(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizing]);
  // Track add/delete
  const handleAddTrack = () => {
    let baseName = 'Track';
    let idx = 1;
    let name = baseName + idx;
    while (tracks.some(t => t.name === name)) {
      idx++;
      name = baseName + idx;
    }
    setTracks(prev => [...prev, { name }]);
    setMidiData(prev => ({ ...prev, [name]: [] }));
    setTrackColors(prev => ({ ...prev, [name]: '#c5e1a5' }));
  };
  const handleDeleteTrack = (name) => {
    if (tracks.length === 1) return;
    setTracks(prev => prev.filter(t => t.name !== name));
    setMidiData(prev => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
    setTrackColors(prev => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
  };
  // DnD reorder
  const handleTrackDragEnd = (result) => {
    if (!result.destination) return;
    const srcIdx = result.source.index;
    const destIdx = result.destination.index;
    if (srcIdx === destIdx) return;
    setTracks(prev => {
      const newTracks = Array.from(prev);
      const [removed] = newTracks.splice(srcIdx, 1);
      newTracks.splice(destIdx, 0, removed);
      return newTracks;
    });
  };

  // Note selection (now stores {track, id})
  const [selectedNotes, setSelectedNotes] = useState([]); // Array<{track, id}>

  // Add note: click on empty cell
  const handleCellClick = (trackName, measure) => {
    // Only add if no overlap
    const overlap = midiData[trackName]?.some(note => {
      const noteEnd = note.start + note.length - 1;
      return (
        (measure >= note.start && measure <= noteEnd) ||
        (measure + 1 >= note.start && measure + 1 <= noteEnd)
      );
    });
    if (overlap) return;
    setMidiData(prev => {
      const next = { ...prev };
      next[trackName] = [
        ...(next[trackName] || []),
        { id: uuidv4(), start: measure, length: 2 },
      ];
      return next;
    });
  };

  // Debug: log midiData changes
  useEffect(() => {
    console.log('midiData changed', midiData);
  }, [midiData]);

  // Dummy state to force re-render
  const [forceUpdate, setForceUpdate] = useState(0);

  // Delete note: Delete key
  // Global keydown event for Delete (register once)
  useEffect(() => {
    const handleKeyDown = (e) => {
      console.log('keydown event', e.key);
      if (e.key === 'Delete' && selectedNotes.length > 0) {
        setMidiData(prev => {
          const next = { ...prev };
          const toDelete = {};
          selectedNotes.forEach(({ track, id }) => {
            if (!toDelete[track]) toDelete[track] = new Set();
            toDelete[track].add(id);
          });
          Object.keys(toDelete).forEach(track => {
            next[track] = next[track].filter(note => !toDelete[track].has(note.id)).map(n => ({...n}));
          });
          return JSON.parse(JSON.stringify(next));
        });
        setSelectedNotes([]);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    console.log('keydown event listener registered');
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      console.log('keydown event listener removed');
    };
  }, []); // Register once

  // Note drag state
  const [dragInfo, setDragInfo] = useState(null); // {startX, movingNotes, originStarts}

  // Start dragging note
  const handleNoteDragStart = (e, track, noteId) => {
    e.stopPropagation();
    // If multi-select, drag all selected, else just this note
    const note = midiData[track].find(n => n.id === noteId);
    const isSelected = selectedNotes.some(sel => sel.track === track && sel.id === noteId);
    let movingNotes;
    if (isSelected) {
      movingNotes = selectedNotes;
    } else {
      movingNotes = [{ track, id: noteId }];
      setSelectedNotes([{ track, id: noteId }]);
    }
    // For each moving note, find its current index in midiData[track]
    const originStarts = movingNotes.map(sel => {
      const idx = midiData[sel.track].findIndex(n => n.id === sel.id);
      return midiData[sel.track][idx]?.start ?? 1;
    });
    setDragInfo({
      startX: e.clientX,
      movingNotes,
      originStarts,
    });
    document.body.style.cursor = 'grabbing';
  };

  // While dragging
  const handleNoteDrag = (e) => {
    if (!dragInfo) return;
    const dx = e.clientX - dragInfo.startX;
    const delta = Math.round(dx / 64); // 1 measure = 64px
    if (delta === 0) return;
    setMidiData(prev => {
      const next = JSON.parse(JSON.stringify(prev));
      dragInfo.movingNotes.forEach((sel, i) => {
        // Find current index by id
        const idx = next[sel.track].findIndex(n => n.id === sel.id);
        if (idx === -1) return;
        const orig = dragInfo.originStarts[i];
        let newStart = orig + delta;
        // Clamp to timeline
        newStart = Math.max(1, Math.min(16 - next[sel.track][idx].length + 1, newStart));
        next[sel.track][idx].start = newStart;
      });
      return next;
    });
  };

  // End dragging
  const handleNoteDragEnd = () => {
    setDragInfo(null);
    document.body.style.cursor = '';
  };

  // Register global drag events
  useEffect(() => {
    if (dragInfo) {
      window.addEventListener('mousemove', handleNoteDrag);
      window.addEventListener('mouseup', handleNoteDragEnd);
      return () => {
        window.removeEventListener('mousemove', handleNoteDrag);
        window.removeEventListener('mouseup', handleNoteDragEnd);
      };
    }
  }, [dragInfo]);

  // Context menu state for note right-click
  const [contextMenu, setContextMenu] = useState(null); // {x, y, track, noteIdx}

  // Handle right-click on note
  const handleNoteContextMenu = (e, track, id) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, track, id });
  };

  // Handle context menu close
  const handleCloseContextMenu = () => setContextMenu(null);

  // Context menu delete (use start/length)
  const handleContextMenuDelete = () => {
    if (!contextMenu) return;
    setMidiData(prev => {
      // Always create new objects/arrays
      const next = JSON.parse(JSON.stringify(prev));
      next[contextMenu.track] = next[contextMenu.track].filter(note => note.id !== contextMenu.id);
      return next;
    });
    setSelectedNotes([]);
    setContextMenu(null);
    setForceUpdate(f => f + 1); // Force re-render
  };

  // Close context menu on click outside or Escape
  useEffect(() => {
    if (!contextMenu) return;
    const handleClick = (e) => setContextMenu(null);
    const handleEsc = (e) => { if (e.key === 'Escape') setContextMenu(null); };
    window.addEventListener('mousedown', handleClick);
    window.addEventListener('keydown', handleEsc);
    return () => {
      window.removeEventListener('mousedown', handleClick);
      window.removeEventListener('keydown', handleEsc);
    };
  }, [contextMenu]);

  // State for note resizing
  const [noteResizing, setNoteResizing] = useState(null); // {track, id, startX, origLength}

  // Mouse events for note resizing
  useEffect(() => {
    if (!noteResizing) return;
    const handleMouseMove = (e) => {
      const dx = e.clientX - noteResizing.startX;
      const delta = Math.round(dx / 64); // 1 measure = 64px
      let newLength = noteResizing.origLength + delta;
      newLength = Math.max(2, newLength); // Always allow shrinking to 2
      // Ensure note does not extend past timeline
      const note = midiData[noteResizing.track].find(n => n.id === noteResizing.id);
      if (note) {
        newLength = Math.min(newLength, 16 - note.start + 1);
      }
      // Debug log
      console.log('Resizing note:', {
        origLength: noteResizing.origLength,
        delta,
        newLength,
        noteStart: note?.start,
        noteId: noteResizing.id
      });
      setMidiData(prev => {
        const next = JSON.parse(JSON.stringify(prev));
        const idx = next[noteResizing.track].findIndex(n => n.id === noteResizing.id);
        if (idx !== -1) {
          next[noteResizing.track][idx].length = newLength;
        }
        return next;
      });
    };
    const handleMouseUp = () => setNoteResizing(null);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [noteResizing, midiData]);

  return (
    <>
      <Box sx={{ width: '100%', overflowX: 'auto', overflow: 'visible', bgcolor: '#f5f5f5', borderRadius: 2, p: 2 }}>
        {/* Timeline header */}
        <Box sx={{ display: 'flex', mb: 1 }}>
          <Box sx={{ width: trackNameWidth }} />
          {measures.map((m) => (
            <Box key={m} sx={{ width: 64, textAlign: 'center', color: '#888', fontSize: 12 }}>{m}</Box>
          ))}
        </Box>
        {/* Track rows with DnD */}
        <DragDropContext onDragEnd={handleTrackDragEnd}>
          <Droppable droppableId="track-list">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                style={{ display: 'flex', flexDirection: 'column', width: '100%' }}
              >
                {tracks.map((track, idx) => (
                  <Draggable key={track.name} draggableId={track.name} index={idx}>
                    {(provided, snapshot) => (
                      <Box
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        sx={{ width: '100%', display: 'flex', alignItems: 'center', mb: 1, opacity: snapshot.isDragging ? 0.7 : 1, zIndex: snapshot.isDragging ? 1 : 'auto', position: snapshot.isDragging ? 'relative' : 'static' }}
                      >
                        {/* Track name + delete + drag handle + resize */}
                        <Paper
                          sx={{
                            width: trackNameWidth,
                            mr: 1,
                            p: 1,
                            pl: 2,
                            pr: 2,
                            textAlign: 'center',
                            bgcolor: snapshot.isDragging ? '#393e46' : '#23272f',
                            fontWeight: 600,
                            border: 'none',
                            transition: 'all 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            boxShadow: snapshot.isDragging ? '0 2px 8px #fbc02d44' : undefined,
                            gap: 1,
                            position: 'relative',
                            userSelect: resizing ? 'none' : undefined,
                          }}
                          onClick={() => setSelectedNotes([])}
                        >
                          <span {...provided.dragHandleProps} style={{ display: 'flex', alignItems: 'center', cursor: 'grab', marginRight: 8 }} title="Drag to reorder">
                            <DragIndicatorIcon sx={{ fontSize: 28, color: '#bdbdbd' }} />
                          </span>
                          <span style={{ flex: 1, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{track.name}</span>
                          <IconButton size="small" onClick={() => handleDeleteTrack(track.name)} disabled={tracks.length === 1}>×</IconButton>
                          {/* Resize handle */}
                          <div
                            style={{
                              width: 8,
                              height: 32,
                              cursor: 'ew-resize',
                              position: 'absolute',
                              right: 0,
                              top: '50%',
                              transform: 'translateY(-50%)',
                              zIndex: 2,
                              background: resizing ? '#fbc02d44' : 'transparent',
                            }}
                            onMouseDown={e => {
                              resizeStartX.current = e.clientX;
                              resizeStartWidth.current = trackNameWidth;
                              setResizing(true);
                            }}
                          />
                        </Paper>
                        {/* Timeline grid for this track */}
                        <Box sx={{ display: 'flex', flex: 1, position: 'relative' }}>
                          {measures.map((m) => (
                            <Box
                              key={m}
                              sx={{
                                width: 64,
                                height: 32,
                                border: '1px solid #bdbdbd',
                                bgcolor: '#e0e0e0', // Much lighter gray for strong contrast with MIDI notes
                                position: 'relative',
                                zIndex: 1,
                                cursor: 'pointer'
                              }}
                              onClick={() => handleCellClick(track.name, m)}
                            />
                          ))}
                          {/* Note bars */}
                          {console.log('Render notes for', track.name, midiData[track.name])}
                          {midiData[track.name]?.map((note, noteIdx) => {
                            const isSelected = selectedNotes.some(sel => sel.track === track.name && sel.id === note.id);
                            return (
                              <Box
                                key={note.id}
                                sx={{
                                  position: 'absolute',
                                  left: (note.start - 1) * 64,
                                  width: note.length * 64 - 8,
                                  height: 24,
                                  top: 4,
                                  bgcolor: trackColors[track.name], // Always use the track color as background
                                  border: isSelected ? '2px solid #fff' : 'none', // White border when selected
                                  borderRadius: 2,
                                  zIndex: 2,
                                  boxShadow: isSelected ? '0 0 0 2px #fbc02d' : '0 1px 4px #0002',
                                  display: 'flex',
                                  alignItems: 'center',
                                  pl: 1,
                                  fontWeight: 500,
                                  fontSize: 14,
                                  color: (track.name === 'Piano') ? '#222' : '#fff', // Usual text color
                                  overflow: 'hidden',
                                  cursor: dragInfo ? 'grabbing' : 'pointer',
                                  transition: 'all 0.2s',
                                  opacity: dragInfo && isSelected ? 0.7 : 1,
                                }}
                                onClick={e => {
                                  e.stopPropagation();
                                  const isMeta = e.metaKey || e.ctrlKey;
                                  if (isMeta) {
                                    setSelectedNotes(prev => {
                                      const exists = prev.some(sel => sel.track === track.name && sel.id === note.id);
                                      if (exists) {
                                        return prev.filter(sel => !(sel.track === track.name && sel.id === note.id));
                                      } else {
                                        return [...prev, { track: track.name, id: note.id }];
                                      }
                                    });
                                  } else {
                                    setSelectedNotes([{ track: track.name, id: note.id }]);
                                  }
                                }}
                                onMouseDown={e => handleNoteDragStart(e, track.name, note.id)}
                                onContextMenu={e => handleNoteContextMenu(e, track.name, note.id)}
                              >
                                {track.name} note
                                {/* Resize handle at right edge of note bar */}
                                <div
                                  style={{
                                    width: 8,
                                    height: 24,
                                    position: 'absolute',
                                    right: 0,
                                    top: 0,
                                    cursor: 'ew-resize',
                                    zIndex: 3,
                                    background: noteResizing && noteResizing.id === note.id ? '#fff8' : 'transparent',
                                    borderRadius: '0 2px 2px 0',
                                  }}
                                  onMouseDown={e => {
                                    e.stopPropagation();
                                    setNoteResizing({
                                      track: track.name,
                                      id: note.id,
                                      startX: e.clientX,
                                      origLength: note.length,
                                    });
                                  }}
                                />
                              </Box>
                            );
                          })}
                        </Box>
                      </Box>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
        {/* Add track button */}
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
          <Button variant="outlined" size="small" onClick={handleAddTrack}>+ Add Track</Button>
        </Box>
      </Box>
      {/* Context menu for note */}
      {contextMenu && (
        <Box
          sx={{
            position: 'fixed',
            left: contextMenu.x,
            top: contextMenu.y,
            zIndex: 9999,
            bgcolor: '#fff',
            border: '1px solid #ccc',
            borderRadius: 1,
            boxShadow: 3,
            minWidth: 120,
            p: 1,
          }}
          onClick={e => e.stopPropagation()}
        >
          <Box
            sx={{
              p: 1,
              cursor: 'pointer',
              color: '#222', // Black text for visibility on white background
              ':hover': { bgcolor: '#ffe082' }
            }}
            onClick={handleContextMenuDelete}
          >
            Delete
          </Box>
        </Box>
      )}
    </>
  );
}

function App() {
  const [result, setResult] = useState('');
  // サイドバーの折りたたみ状態
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const handleSidebarToggle = () => setSidebarCollapsed((prev) => !prev);

  // Sidebar width state for resizable sidebar
  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_WIDTH); // Default 240px
  const [sidebarResizing, setSidebarResizing] = useState(false);
  const sidebarResizeStartX = useRef(null);
  const sidebarResizeStartWidth = useRef(null);

  // Mouse events for sidebar resizing
  useEffect(() => {
    if (!sidebarResizing) return;
    const handleMouseMove = (e) => {
      const dx = e.clientX - sidebarResizeStartX.current;
      let newWidth = sidebarResizeStartWidth.current + dx;
      newWidth = Math.max(120, Math.min(400, newWidth)); // Min 120px, Max 400px
      setSidebarWidth(newWidth);
    };
    const handleMouseUp = () => setSidebarResizing(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [sidebarResizing]);

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
                width: sidebarCollapsed ? SIDEBAR_COLLAPSED_WIDTH : sidebarWidth, // Use resizable width
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
                userSelect: sidebarResizing ? 'none' : undefined,
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
              {/* Resize handle at the right edge of the sidebar */}
              {!sidebarCollapsed && (
                <div
                  style={{
                    width: 8,
                    height: '100%',
                    cursor: 'ew-resize',
                    position: 'absolute',
                    right: 0,
                    top: 0,
                    zIndex: 2,
                    background: sidebarResizing ? '#00adb544' : 'transparent',
                  }}
                  onMouseDown={e => {
                    sidebarResizeStartX.current = e.clientX;
                    sidebarResizeStartWidth.current = sidebarWidth;
                    setSidebarResizing(true);
                  }}
                />
              )}
            </Paper>
            {/* メインコンテンツ */}
            <Box
              sx={{
                flex: 1,
                ml: sidebarCollapsed ? `${SIDEBAR_COLLAPSED_WIDTH}px` : `${sidebarWidth}px`, // Match margin-left to sidebar width
                transition: 'margin-left 0.2s',
                p: { xs: 1, sm: 3 }
              }}
            >
              {/* DAW timeline and track layout */}
              <TimelineTracks />
              {/* Other screens can be added here in the future */}
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
