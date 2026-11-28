#include "Phrase.h"
#include "Link.h"
#include "MidiFile.h"
#import <AudioUnit/AUCocoaUIView.h>
#import <Cocoa/Cocoa.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#include <algorithm>
#include <cmath>
#include <memory>
#include <vector>

@protocol MerlaiMIDIDragSource <NSObject>
- (NSURL *)midiDragURL;
@end

@interface MerlaiButton : NSButton @end
@implementation MerlaiButton
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
@end

@interface MerlaiPopUpButton : NSPopUpButton @end
@implementation MerlaiPopUpButton
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
@end

@interface MerlaiSegmentedControl : NSSegmentedControl @end
@implementation MerlaiSegmentedControl
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
@end

@interface MerlaiTextField : NSTextField @end
@implementation MerlaiTextField
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
@end

@interface MerlaiMIDIDragView : NSView <NSDraggingSource>
@property(nonatomic, weak) id<MerlaiMIDIDragSource> source;
@property(nonatomic) BOOL enabled;
@property(nonatomic) BOOL confirmed;
@end

@implementation MerlaiMIDIDragView
- (BOOL)isFlipped { return YES; }
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
- (void)setEnabled:(BOOL)enabled { _enabled = enabled; [self setNeedsDisplay:YES]; }
- (void)setConfirmed:(BOOL)confirmed { _confirmed = confirmed; [self setNeedsDisplay:YES]; }
- (void)drawRect:(NSRect)dirtyRect {
  NSColor *fill = self.enabled
    ? [NSColor colorWithRed:.16 green:.43 blue:.76 alpha:1]
    : [NSColor colorWithWhite:.28 alpha:1];
  [fill setFill];
  [[NSBezierPath bezierPathWithRoundedRect:NSInsetRect(self.bounds, .5, .5)
                                    xRadius:6 yRadius:6] fill];
  NSDictionary *style = @{NSFontAttributeName: [NSFont systemFontOfSize:12 weight:NSFontWeightSemibold],
    NSForegroundColorAttributeName: self.enabled ? NSColor.whiteColor : NSColor.disabledControlTextColor};
  NSString *text = self.confirmed
    ? @"↗ 確定版をLogicへドラッグ"
    : @"↗ 未確定候補をLogicへドラッグ";
  NSSize size = [text sizeWithAttributes:style];
  [text drawAtPoint:NSMakePoint((NSWidth(self.bounds) - size.width) / 2,
                                (NSHeight(self.bounds) - size.height) / 2)
      withAttributes:style];
}
- (void)resetCursorRects {
  [self addCursorRect:self.bounds cursor:self.enabled ? NSCursor.openHandCursor : NSCursor.arrowCursor];
}
- (id<NSPasteboardWriting>)dragPasteboardWriter {
  NSURL *url = [self.source midiDragURL];
  if (!url) return nil;
  NSPasteboardItem *item = [[NSPasteboardItem alloc] init];
  [item setString:url.absoluteString forType:NSPasteboardTypeFileURL];
  return item;
}
- (void)beginMIDIDrag:(NSEvent *)event {
  if (!self.enabled) return;
  id<NSPasteboardWriting> writer = [self dragPasteboardWriter];
  if (!writer) return;
  NSDraggingItem *drag = [[NSDraggingItem alloc] initWithPasteboardWriter:writer];
  NSImage *image = [NSWorkspace.sharedWorkspace iconForContentType:UTTypeMIDI];
  NSPoint point = [self convertPoint:event.locationInWindow fromView:nil];
  [drag setDraggingFrame:NSMakeRect(point.x - 16, point.y - 16, 32, 32) contents:image];
  [self beginDraggingSessionWithItems:@[drag] event:event source:self];
}
- (void)mouseDown:(NSEvent *)event { [self beginMIDIDrag:event]; }
- (NSDragOperation)draggingSession:(NSDraggingSession *)session
 sourceOperationMaskForDraggingContext:(NSDraggingContext)context {
  return NSDragOperationCopy;
}
@end

@interface MerlaiPromptPlaceholder : NSTextField
@property(nonatomic, weak) NSTextView *editor;
@end
@implementation MerlaiPromptPlaceholder
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
- (void)mouseDown:(NSEvent *)event { [self.window makeFirstResponder:self.editor]; }
@end

@interface MerlaiPromptTextView : NSTextView
@property(nonatomic, copy) NSString *placeholderString;
@property(nonatomic, weak) NSTextField *placeholderLabel;
@end
@implementation MerlaiPromptTextView
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
- (void)setPlaceholderString:(NSString *)placeholderString {
  _placeholderString = [placeholderString copy];
  self.placeholderLabel.stringValue = _placeholderString ?: @"";
  [self updatePlaceholder];
}
- (void)setPlaceholderLabel:(NSTextField *)placeholderLabel {
  _placeholderLabel = placeholderLabel;
  _placeholderLabel.stringValue = _placeholderString ?: @"";
  [self updatePlaceholder];
}
- (void)setString:(NSString *)string {
  [super setString:string];
  [self updatePlaceholder];
}
- (void)didChangeText {
  [super didChangeText];
  [self updatePlaceholder];
}
- (void)updatePlaceholder {
  self.placeholderLabel.hidden = self.string.length > 0 || !_placeholderString.length;
}
@end

static BOOL MerlaiIsEditingTextInView(NSView *root) {
  NSResponder *responder = root.window.firstResponder;
  if (![responder isKindOfClass:NSTextView.class]) return NO;
  NSTextView *textView = (NSTextView *)responder;
  if (textView == root || [textView isDescendantOf:root]) return YES;

  // NSTextField edits through the window's shared field editor, which is not
  // a descendant of the control. Its delegate identifies the owning field.
  id delegate = textView.delegate;
  return [delegate isKindOfClass:NSView.class] &&
    (delegate == root || [(NSView *)delegate isDescendantOf:root]);
}

static NSString *BeatLabel(double beat) {
  NSInteger bar = (NSInteger)floor(beat / 4.0) + 1;
  NSInteger within = (NSInteger)floor(fmod(std::max(0.0, beat), 4.0)) + 1;
  return [NSString stringWithFormat:@"%ld.%ld", (long)bar, (long)within];
}
static NSString *NoteLabel(uint8_t pitch) {
  static NSArray<NSString *> *names = @[@"C", @"C♯", @"D", @"E♭", @"E", @"F",
    @"F♯", @"G", @"A♭", @"A", @"B♭", @"B"];
  return [NSString stringWithFormat:@"%@%d", names[pitch % 12], pitch / 12 - 1];
}
static NSString *PhraseSummary(const Phrase &phrase) {
  if (!phrase.count) return @"0音";
  uint8_t low = 127, high = 0;
  for (uint32_t i = 0; i < phrase.count; ++i) {
    low = std::min(low, phrase.notes[i].pitch);
    high = std::max(high, phrase.notes[i].pitch);
  }
  return [NSString stringWithFormat:@"%u音・%@〜%@", phrase.count,
    NoteLabel(low), NoteLabel(high)];
}

@interface MerlaiPianoRoll : NSView {
  Phrase _original, _proposal;
  BOOL _hasOriginal, _hasProposal;
  BOOL _editable, _dragging, _resizing, _savedDragUndo;
  NSInteger _selected;
  NSPoint _dragOrigin;
  Note _dragNote;
  uint8_t _displayLow, _displayHigh;
  std::vector<Phrase> _editUndo;
  __weak id _changeTarget;
  SEL _changeAction;
}
- (void)setOriginal:(const Phrase &)p;
- (void)setProposal:(const Phrase &)p visible:(BOOL)visible;
- (void)clear;
- (void)setEditable:(BOOL)editable target:(id)target action:(SEL)action;
- (Phrase)proposal;
- (void)undoCandidate;
@end

@implementation MerlaiPianoRoll
- (BOOL)isFlipped { return YES; }
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
- (BOOL)acceptsFirstResponder { return _editable; }
- (void)setOriginal:(const Phrase &)p {
  _original = p; _hasOriginal = YES; [self setNeedsDisplay:YES];
}
- (void)setProposal:(const Phrase &)p visible:(BOOL)visible {
  _proposal = p; _hasProposal = visible; _selected = -1; _editUndo.clear();
  [self setNeedsDisplay:YES];
}
- (void)clear {
  _hasOriginal = _hasProposal = NO; [self setNeedsDisplay:YES];
}
- (void)setEditable:(BOOL)editable target:(id)target action:(SEL)action {
  _editable = editable; _changeTarget = target; _changeAction = action; _selected = -1;
}
- (Phrase)proposal { return _proposal; }
- (void)notifyChange {
  [self setNeedsDisplay:YES];
  if (_changeTarget && _changeAction) [NSApp sendAction:_changeAction to:_changeTarget from:self];
}
- (NSRect)proposalLane {
  NSRect plot = NSInsetRect(self.bounds, 8, 7); plot.origin.x += 72; plot.size.width -= 72;
  CGFloat h = (plot.size.height - 8) / 2;
  return NSMakeRect(plot.origin.x, plot.origin.y + h + 8, plot.size.width, h);
}
- (NSRect)noteRect:(const Note &)note lane:(NSRect)lane {
  double duration = std::max(0.001, _proposal.end - _proposal.start);
  double pitchSpan = std::max<int>(5, _displayHigh - _displayLow + 1);
  CGFloat x = lane.origin.x + lane.size.width * note.start / duration;
  CGFloat width = std::max<CGFloat>(5, lane.size.width * (note.end - note.start) / duration);
  CGFloat y = lane.origin.y + 3 + (_displayHigh - note.pitch) / pitchSpan * (lane.size.height - 12);
  return NSMakeRect(x, y, width, 8);
}
- (void)mouseDown:(NSEvent *)event {
  if (!_editable || !_hasProposal) return [super mouseDown:event];
  [self.window makeFirstResponder:self];
  NSPoint point = [self convertPoint:event.locationInWindow fromView:nil];
  NSRect lane = [self proposalLane]; _selected = -1;
  for (NSInteger i = (NSInteger)_proposal.count - 1; i >= 0; --i) {
    NSRect rect = NSInsetRect([self noteRect:_proposal.notes[i] lane:lane], -3, -3);
    if (NSPointInRect(point, rect)) {
      _selected = i; _dragging = YES; _dragOrigin = point; _dragNote = _proposal.notes[i];
      _resizing = point.x >= NSMaxX(rect) - 9; _savedDragUndo = NO; break;
    }
  }
  [self setNeedsDisplay:YES];
}
- (void)mouseDragged:(NSEvent *)event {
  if (!_dragging || _selected < 0 || _selected >= (NSInteger)_proposal.count) return;
  NSPoint point = [self convertPoint:event.locationInWindow fromView:nil];
  NSRect lane = [self proposalLane]; double span = _proposal.end - _proposal.start;
  if (!_savedDragUndo) { _editUndo.push_back(_proposal); _savedDragUndo = YES; }
  double beatDelta = (point.x - _dragOrigin.x) / lane.size.width * span;
  double pitchSpan = std::max<int>(5, _displayHigh - _displayLow + 1);
  int pitchDelta = (int)std::lround(-(point.y - _dragOrigin.y) / (lane.size.height - 12) * pitchSpan);
  bool snap = !(event.modifierFlags & NSEventModifierFlagOption);
  auto quantize = [&](double value) { return snap ? std::round(value * 4.) / 4. : value; };
  Note note = _dragNote;
  if (_resizing) {
    note.end = std::clamp(quantize(_dragNote.end + beatDelta), note.start + 0.01, span);
  } else {
    double length = note.end - note.start;
    note.start = std::clamp(quantize(_dragNote.start + beatDelta), 0., std::max(0., span - length));
    note.end = note.start + length;
    note.pitch = (uint8_t)std::clamp<int>((int)_dragNote.pitch + pitchDelta, 0, 127);
  }
  _proposal.notes[_selected] = note; [self notifyChange];
}
- (void)mouseUp:(NSEvent *)event { _dragging = NO; _savedDragUndo = NO; }
- (void)keyDown:(NSEvent *)event {
  if ((event.modifierFlags & NSEventModifierFlagCommand) &&
      [event.charactersIgnoringModifiers.lowercaseString isEqual:@"z"]) {
    [self undoCandidate]; return;
  }
  if ((event.keyCode == 51 || event.keyCode == 117) && _selected >= 0 &&
      _selected < (NSInteger)_proposal.count) {
    _editUndo.push_back(_proposal);
    for (uint32_t i = (uint32_t)_selected; i + 1 < _proposal.count; ++i)
      _proposal.notes[i] = _proposal.notes[i + 1];
    --_proposal.count; _selected = -1; [self notifyChange]; return;
  }
  [super keyDown:event];
}
- (void)undoCandidate {
  if (_editUndo.empty()) return;
  _proposal = _editUndo.back(); _editUndo.pop_back(); _selected = -1; [self notifyChange];
}
- (void)drawPhrase:(const Phrase &)p rect:(NSRect)r color:(NSColor *)color
                 low:(uint8_t)low high:(uint8_t)high {
  if (!p.count || p.end <= p.start) return;
  double duration = p.end - p.start, pitchSpan = std::max<int>(5, high - low + 1);
  [color setFill];
  for (uint32_t i = 0; i < p.count; ++i) {
    const Note &n = p.notes[i];
    CGFloat x = r.origin.x + r.size.width * n.start / duration;
    CGFloat w = std::max<CGFloat>(3, r.size.width * (n.end - n.start) / duration);
    CGFloat y = r.origin.y + 3 + (high - n.pitch) / pitchSpan * (r.size.height - 12);
    [[NSBezierPath bezierPathWithRoundedRect:NSMakeRect(x, y, w, 7)
                                      xRadius:2 yRadius:2] fill];
  }
}
- (void)drawRect:(NSRect)dirty {
  [[NSColor colorWithWhite:0.10 alpha:1] setFill]; NSRectFill(self.bounds);
  NSDictionary *style = @{
    NSFontAttributeName: [NSFont systemFontOfSize:11 weight:NSFontWeightSemibold],
    NSForegroundColorAttributeName: [NSColor colorWithWhite:0.78 alpha:1]
  };
  NSRect plot = NSInsetRect(self.bounds, 8, 7);
  plot.origin.x += 72; plot.size.width -= 72;
  CGFloat h = (plot.size.height - 8) / 2;
  NSRect top = NSMakeRect(plot.origin.x, plot.origin.y, plot.size.width, h);
  NSRect bottom = NSMakeRect(plot.origin.x, NSMaxY(top) + 8, plot.size.width, h);
  [@"原案" drawAtPoint:NSMakePoint(12, NSMidY(top) - 7) withAttributes:style];
  [@"修正案" drawAtPoint:NSMakePoint(12, NSMidY(bottom) - 7) withAttributes:style];
  for (NSValue *value in @[[NSValue valueWithRect:top], [NSValue valueWithRect:bottom]]) {
    NSRect lane = value.rectValue;
    [[NSColor colorWithWhite:0.18 alpha:1] setFill]; NSRectFill(lane);
    for (NSInteger i = 0; i <= 8; ++i) {
      CGFloat x = lane.origin.x + lane.size.width * i / 8;
      [[NSColor colorWithWhite:(i % 4 == 0 ? 0.38 : 0.27) alpha:1] setStroke];
      [NSBezierPath strokeLineFromPoint:NSMakePoint(x, lane.origin.y)
                                toPoint:NSMakePoint(x, NSMaxY(lane))];
    }
  }
  uint8_t low = 127, high = 0;
  auto include = [&](const Phrase &phrase, BOOL present) {
    if (!present) return;
    for (uint32_t i = 0; i < phrase.count; ++i) {
      low = std::min(low, phrase.notes[i].pitch);
      high = std::max(high, phrase.notes[i].pitch);
    }
  };
  include(_original, _hasOriginal); include(_proposal, _hasProposal);
  if (low > high) { low = 60; high = 72; }
  _displayLow = low > 3 ? low - 3 : 0; _displayHigh = std::min<int>(127, high + 3);
  if (_hasOriginal)
    [self drawPhrase:_original rect:top
               color:[NSColor colorWithRed:.30 green:.68 blue:1 alpha:1] low:_displayLow high:_displayHigh];
  if (_hasProposal)
    [self drawPhrase:_proposal rect:bottom
               color:[NSColor colorWithRed:1 green:.55 blue:.28 alpha:1] low:_displayLow high:_displayHigh];
  else {
    NSDictionary *empty = @{NSFontAttributeName: [NSFont systemFontOfSize:11],
      NSForegroundColorAttributeName: [NSColor colorWithWhite:.55 alpha:1]};
    [@"指示を確認すると表示されます"
        drawAtPoint:NSMakePoint(bottom.origin.x + 10, bottom.origin.y + 9)
      withAttributes:empty];
  }
  if (_editable && _selected >= 0 && _selected < (NSInteger)_proposal.count) {
    [[NSColor whiteColor] setStroke];
    NSBezierPath *selection = [NSBezierPath bezierPathWithRoundedRect:
      NSInsetRect([self noteRect:_proposal.notes[_selected] lane:[self proposalLane]], -2, -2)
      xRadius:2 yRadius:2];
    selection.lineWidth = 2; [selection stroke];
  }
}
@end

@interface MerlaiPhrasePanel : NSView <MerlaiMIDIDragSource, NSTextViewDelegate> {
  AudioUnit _unit;
  Phrase _original, _current, _draft;
  std::vector<Phrase> _undo;
  MerlaiPromptTextView *_instruction;
  NSTextField *_message, *_captureSummary, *_activeSource;
  NSTextView *_assistantMessage;
  NSTextField *_sourceName;
  NSTextField *_endpointField;
  MerlaiPopUpButton *_sourcePopup, *_purposePopup, *_keyScalePopup, *_providerPopup, *_modelPopup;
  NSButton *_plan, *_generateButton, *_apply, *_originalButton, *_revisedButton, *_undoButton,
    *_builtinButton;
  NSButton *_cancelButton;
  NSButton *_saveMIDIButton, *_showMIDIButton, *_editorRevisedButton, *_editorApplyButton;
  MerlaiMIDIDragView *_midiDragView;
  NSProgressIndicator *_progress;
  MerlaiPianoRoll *_roll, *_editorRoll;
  NSView *_generationView, *_editorView, *_assistantPanel;
  MerlaiSegmentedControl *_tabs;
  NSTimer *_timer;
  NSTimer *_generationTimer;
  NSTask *_modelTask;
  NSDate *_generationStarted;
  NSString *_generationStage;
  NSArray<NSString *> *_suggestions;
  NSArray<MerlaiButton *> *_suggestionButtons;
  uint64_t _instanceId, _sourcesSignature;
  uint64_t _generationRevision;
  uint64_t _loadedSourceId, _loadedSourceRevision;
  NSString *_loadedSourceName, *_loadedSourceKind;
  NSArray<NSDictionary *> *_providers;
  bool _loaded, _hasDraft, _forceBuiltinOnce;
  NSURL *_lastMIDIURL;
  BOOL _auditioningRevised;
#if defined(MERLAI_UI_TESTING)
  BOOL _useTestCapture;
  CaptureInfo _testCapture;
  Phrase _testCapturedPhrase;
  NSUInteger _testSourceRefreshes;
#endif
}
- (instancetype)initWithUnit:(AudioUnit)unit;
@end

@implementation MerlaiPhrasePanel
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
- (NSButton *)button:(NSString *)title action:(SEL)action frame:(NSRect)frame {
  MerlaiButton *b = [[MerlaiButton alloc] initWithFrame:frame];
  b.title = title; b.target = self; b.action = action;
  b.bezelStyle = NSBezelStyleRounded; [_generationView addSubview:b];
  return b;
}
- (NSButton *)editorButton:(NSString *)title action:(SEL)action {
  MerlaiButton *button = [[MerlaiButton alloc] initWithFrame:NSZeroRect];
  button.title = title; button.target = self; button.action = action;
  return button;
}
- (NSTextField *)label:(NSString *)text frame:(NSRect)frame
                  size:(CGFloat)size bold:(BOOL)bold {
  NSTextField *l = [NSTextField labelWithString:text];
  l.frame = frame;
  l.font = [NSFont systemFontOfSize:size
                            weight:(bold ? NSFontWeightSemibold : NSFontWeightRegular)];
  l.textColor = [NSColor colorWithWhite:.82 alpha:1];
  [_generationView addSubview:l]; return l;
}
- (instancetype)initWithUnit:(AudioUnit)unit {
  if ((self = [super initWithFrame:NSMakeRect(0, 0, 960, 720)])) {
    self.wantsLayer = YES;
    self.layer.backgroundColor = [NSColor colorWithWhite:.13 alpha:1].CGColor;
    _generationView = [[NSView alloc] initWithFrame:NSMakeRect(0, 0, 960, 672)];
    _generationView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    _generationView.accessibilityIdentifier = @"merlai.generation";
    [self addSubview:_generationView];
    _unit = unit;
    UInt32 idSize = sizeof(_instanceId);
    AudioUnitGetProperty(_unit, InstanceID, 0, 0, &_instanceId, &idSize);
    [self label:@"Merlai フレーズ生成" frame:NSMakeRect(16, 588, 220, 24) size:17 bold:YES];
    [self label:@"1  入力を選ぶ" frame:NSMakeRect(240, 590, 100, 20) size:12 bold:YES];
    [self label:@"2  取り込む" frame:NSMakeRect(345, 590, 90, 20) size:12 bold:YES];
    [self label:@"3  候補を作る" frame:NSMakeRect(440, 590, 105, 20) size:12 bold:YES];
    [self label:@"4  確定・配置" frame:NSMakeRect(550, 590, 110, 20) size:12 bold:YES];
    [self button:@"2  フレーズを取り込む" action:@selector(arm:)
           frame:NSMakeRect(16, 543, 185, 32)];
    _captureSummary = [self label:@"未取り込み — Logicで先にサイクルを指定"
                            frame:NSMakeRect(216, 550, 480, 20) size:12 bold:NO];
    _captureSummary.accessibilityIdentifier = @"merlai.capture-summary";
    _progress = [[NSProgressIndicator alloc] initWithFrame:NSMakeRect(216, 539, 480, 8)];
    _progress.accessibilityIdentifier = @"merlai.capture-progress";
    _progress.minValue = 0; _progress.maxValue = 1; _progress.indeterminate = NO;
    [_generationView addSubview:_progress];
    [self label:@"共有名" frame:NSMakeRect(16, 507, 48, 20) size:11 bold:YES];
    _sourceName = [[MerlaiTextField alloc] initWithFrame:NSMakeRect(64, 500, 112, 27)];
    _sourceName.accessibilityIdentifier = @"merlai.source-name";
    _sourceName.stringValue = [NSString stringWithFormat:@"Merlai %llu",
      (unsigned long long)_instanceId];
    _sourceName.target = self; _sourceName.action = @selector(renameSource:);
    [_generationView addSubview:_sourceName];
    _sourcePopup = [[MerlaiPopUpButton alloc] initWithFrame:NSMakeRect(184, 500, 160, 27)];
    _sourcePopup.accessibilityIdentifier = @"merlai.source";
    [_sourcePopup addItemWithTitle:@"入力元: このトラック"];
    [_generationView addSubview:_sourcePopup];
    [self button:@"入力を読み込む" action:@selector(loadSource:)
           frame:NSMakeRect(350, 500, 98, 27)];
    _purposePopup = [[MerlaiPopUpButton alloc] initWithFrame:NSMakeRect(454, 500, 120, 27)];
    _purposePopup.accessibilityIdentifier = @"merlai.purpose";
    [_purposePopup addItemsWithTitles:@[@"編集", @"ベース", @"コード", @"対旋律", @"続きを生成"]];
    [_generationView addSubview:_purposePopup];
    _keyScalePopup = [[MerlaiPopUpButton alloc] initWithFrame:NSMakeRect(580, 500, 116, 27)];
    _keyScalePopup.accessibilityIdentifier = @"merlai.key-scale";
    [_keyScalePopup addItemWithTitle:@"Key: 未指定"];
    NSArray *roots = @[@"C", @"C♯", @"D", @"E♭", @"E", @"F", @"F♯", @"G", @"A♭", @"A", @"B♭", @"B"];
    for (NSUInteger root = 0; root < roots.count; ++root) {
      for (NSUInteger scale = 1; scale <= 2; ++scale) {
        [_keyScalePopup addItemWithTitle:[NSString stringWithFormat:@"%@ %@", roots[root],
          scale == 1 ? @"Major" : @"Minor"]];
        _keyScalePopup.lastItem.representedObject = @{@"root": @(root), @"scale": @(scale)};
      }
    }
    [_generationView addSubview:_keyScalePopup];
    [self label:@"モデル" frame:NSMakeRect(16, 467, 44, 20) size:11 bold:YES];
    _providerPopup = [[MerlaiPopUpButton alloc] initWithFrame:NSMakeRect(64, 460, 170, 27)];
    _providerPopup.accessibilityIdentifier = @"merlai.provider";
    [_providerPopup addItemWithTitle:@"内蔵ルール"];
    _providerPopup.target = self; _providerPopup.action = @selector(providerChanged:);
    [_generationView addSubview:_providerPopup];
    _modelPopup = [[MerlaiPopUpButton alloc] initWithFrame:NSMakeRect(242, 460, 170, 27)];
    _modelPopup.accessibilityIdentifier = @"merlai.model";
    [_modelPopup addItemWithTitle:@"自動"];
    [_generationView addSubview:_modelPopup];
    _endpointField = [[MerlaiTextField alloc] initWithFrame:NSMakeRect(420, 460, 180, 27)];
    _endpointField.accessibilityIdentifier = @"merlai.endpoint";
    _endpointField.placeholderString = @"ローカル互換URL（任意）";
    _endpointField.stringValue = [[NSUserDefaults standardUserDefaults]
      stringForKey:@"MerlaiModelEndpoint"] ?: @"";
    [_generationView addSubview:_endpointField];
    [self button:@"再検出" action:@selector(refreshProviders:)
           frame:NSMakeRect(608, 460, 88, 27)];
    _activeSource = [self label:@"使用中: 未読み込み" frame:NSMakeRect(16, 438, 680, 18)
                           size:11 bold:NO];
    _roll = [[MerlaiPianoRoll alloc] initWithFrame:NSMakeRect(16, 270, 680, 165)];
    _roll.wantsLayer = YES; _roll.layer.cornerRadius = 5;
    _roll.layer.masksToBounds = YES; [_generationView addSubview:_roll];
    [self label:@"3  候補を生成、または文章で編集" frame:NSMakeRect(16, 246, 260, 22) size:13 bold:YES];
    NSScrollView *promptScroll = [[NSScrollView alloc]
      initWithFrame:NSMakeRect(16, 188, 355, 52)];
    promptScroll.borderType = NSBezelBorder;
    promptScroll.hasVerticalScroller = YES;
    promptScroll.drawsBackground = YES;
    _instruction = [[MerlaiPromptTextView alloc]
      initWithFrame:promptScroll.contentView.bounds];
    _instruction.string = @"後半だけ音数を半分に。最後の音は残して";
    _instruction.font = [NSFont systemFontOfSize:13];
    _instruction.verticallyResizable = YES;
    _instruction.horizontallyResizable = NO;
    _instruction.autoresizingMask = NSViewWidthSizable;
    _instruction.textContainer.widthTracksTextView = YES;
    _instruction.textContainer.containerSize = NSMakeSize(
      promptScroll.contentSize.width, CGFLOAT_MAX);
    _instruction.placeholderString = @"作曲・編集の指示を入力";
    _instruction.delegate = self;
    _instruction.accessibilityLabel = @"生成指示";
    _instruction.accessibilityIdentifier = @"merlai.instruction";
    promptScroll.documentView = _instruction;
    [_generationView addSubview:promptScroll];
    MerlaiPromptPlaceholder *placeholder = [[MerlaiPromptPlaceholder alloc]
      initWithFrame:NSMakeRect(22, 192, 340, 20)];
    placeholder.stringValue = _instruction.placeholderString;
    placeholder.font = _instruction.font;
    placeholder.textColor = NSColor.placeholderTextColor;
    placeholder.drawsBackground = NO;
    placeholder.accessibilityElement = NO;
    placeholder.accessibilityIdentifier = @"merlai.instruction-placeholder";
    placeholder.editor = _instruction;
    _instruction.placeholderLabel = placeholder;
    [_generationView addSubview:placeholder];
    _plan = [self button:@"変更内容を確認" action:@selector(plan:)
                   frame:NSMakeRect(379, 208, 145, 30)];
    _plan.accessibilityIdentifier = @"merlai.plan";
    _generateButton = [self button:@"候補を生成" action:@selector(generate:)
                              frame:NSMakeRect(532, 208, 164, 30)];
    _generateButton.accessibilityIdentifier = @"merlai.generate";
    _originalButton = [self button:@"原案を聴く" action:@selector(original:)
                             frame:NSMakeRect(16, 163, 112, 30)];
    _revisedButton = [self button:@"修正案を聴く" action:@selector(revised:)
                            frame:NSMakeRect(136, 163, 120, 30)];
    _originalButton.buttonType = NSButtonTypeToggle;
    _revisedButton.buttonType = NSButtonTypeToggle;
    _apply = [self button:@"候補を確定" action:@selector(apply:)
                    frame:NSMakeRect(264, 163, 190, 30)];
    _undoButton = [self button:@"一手戻す" action:@selector(undoEdit:)
                         frame:NSMakeRect(462, 163, 100, 30)];
    _builtinButton = [self button:@"内蔵で生成" action:@selector(generateBuiltin:)
                            frame:NSMakeRect(570, 163, 126, 30)];
    _builtinButton.hidden = YES;
    _cancelButton = [self button:@"生成を中止" action:@selector(cancelGeneration:)
                           frame:NSMakeRect(570, 163, 126, 30)];
    _cancelButton.hidden = YES;
    _midiDragView = [[MerlaiMIDIDragView alloc] initWithFrame:NSMakeRect(16, 126, 240, 30)];
    _midiDragView.source = self; _midiDragView.enabled = NO;
    _midiDragView.accessibilityLabel = @"候補をLogicへドラッグ";
    _midiDragView.accessibilityIdentifier = @"merlai.midi-drag";
    [_generationView addSubview:_midiDragView];
    _saveMIDIButton = [self button:@"MIDIを保存" action:@selector(saveMIDI:)
                                 frame:NSMakeRect(264, 126, 112, 30)];
    _showMIDIButton = [self button:@"Finderで表示" action:@selector(showMIDI:)
                                 frame:NSMakeRect(384, 126, 120, 30)];
    _saveMIDIButton.enabled = _showMIDIButton.enabled = NO;
    _apply.enabled = _plan.enabled = _originalButton.enabled =
        _revisedButton.enabled = _undoButton.enabled = NO;
    _message = [NSTextField wrappingLabelWithString:
      @"操作: ① Logicで黄色いサイクル範囲を指定  ② 取り込むを押す  ③ サイクル先頭から一周再生"];
    _message.frame = NSMakeRect(16, 60, 680, 62);
    _message.font = [NSFont systemFontOfSize:12];
    _message.textColor = [NSColor colorWithWhite:.86 alpha:1];
    [_generationView addSubview:_message];
    _assistantPanel = [[NSView alloc] initWithFrame:NSMakeRect(712, 126, 232, 309)];
    _assistantPanel.wantsLayer = YES;
    _assistantPanel.layer.backgroundColor = [NSColor colorWithWhite:.17 alpha:1].CGColor;
    _assistantPanel.layer.cornerRadius = 6;
    _assistantPanel.accessibilityIdentifier = @"merlai.assistant-panel";
    [_generationView addSubview:_assistantPanel];
    NSTextField *assistantTitle = [NSTextField labelWithString:@"LLMの提案"];
    assistantTitle.frame = NSMakeRect(12, 279, 208, 20);
    assistantTitle.font = [NSFont systemFontOfSize:12 weight:NSFontWeightSemibold];
    assistantTitle.textColor = NSColor.lightGrayColor;
    [_assistantPanel addSubview:assistantTitle];
    NSScrollView *assistantScroll = [[NSScrollView alloc] initWithFrame:NSMakeRect(10, 102, 212, 173)];
    assistantScroll.borderType = NSNoBorder;
    assistantScroll.hasVerticalScroller = YES;
    assistantScroll.drawsBackground = NO;
    _assistantMessage = [[NSTextView alloc] initWithFrame:assistantScroll.contentView.bounds];
    _assistantMessage.editable = NO; _assistantMessage.selectable = YES;
    _assistantMessage.drawsBackground = NO;
    _assistantMessage.font = [NSFont systemFontOfSize:11];
    _assistantMessage.textColor = [NSColor colorWithRed:.75 green:.86 blue:1 alpha:1];
    _assistantMessage.string = @"候補を生成すると、モデルの説明と次の提案をここに表示します。";
    _assistantMessage.accessibilityLabel = @"LLMからの説明";
    _assistantMessage.accessibilityIdentifier = @"merlai.assistant-message";
    _assistantMessage.verticallyResizable = YES; _assistantMessage.horizontallyResizable = NO;
    _assistantMessage.textContainer.widthTracksTextView = YES;
    assistantScroll.documentView = _assistantMessage;
    [_assistantPanel addSubview:assistantScroll];
    NSMutableArray *suggestionButtons = [NSMutableArray arrayWithCapacity:3];
    for (NSUInteger i = 0; i < 3; ++i) {
      MerlaiButton *button = [[MerlaiButton alloc] initWithFrame:NSMakeRect(10, 70 - i * 32, 212, 26)];
      button.bezelStyle = NSBezelStyleRounded; button.target = self;
      button.action = @selector(useSuggestion:); button.tag = 7100 + i; button.hidden = YES;
      button.font = [NSFont systemFontOfSize:10];
      button.accessibilityIdentifier = [NSString stringWithFormat:@"merlai.suggestion.%lu",
        (unsigned long)i];
      [_assistantPanel addSubview:button]; [suggestionButtons addObject:button];
    }
    _suggestionButtons = suggestionButtons;
    _tabs = [[MerlaiSegmentedControl alloc] initWithFrame:NSMakeRect(16, 682, 300, 28)];
    _tabs.segmentCount = 2; [_tabs setLabel:@"生成" forSegment:0];
    [_tabs setLabel:@"候補差分" forSegment:1]; _tabs.selectedSegment = 0;
    _tabs.accessibilityLabel = @"表示モード";
    _tabs.accessibilityIdentifier = @"merlai.tabs";
    _tabs.target = self; _tabs.action = @selector(changeTab:); [self addSubview:_tabs];
    _editorView = [[NSView alloc] initWithFrame:NSMakeRect(0, 0, 960, 672)];
    _editorView.hidden = YES; _editorView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    _editorView.accessibilityIdentifier = @"merlai.editor";
    _editorView.wantsLayer = YES; _editorView.layer.backgroundColor =
      [NSColor colorWithWhite:.13 alpha:1].CGColor; [self addSubview:_editorView];
    NSTextField *editorTitle = [NSTextField labelWithString:
      @"青い原案とオレンジの候補を比較します。詳細なノート編集はLogicで行います。"];
    editorTitle.frame = NSMakeRect(16, 636, 720, 22); editorTitle.textColor = NSColor.lightGrayColor;
    [_editorView addSubview:editorTitle];
    _editorRoll = [[MerlaiPianoRoll alloc] initWithFrame:NSMakeRect(16, 76, 928, 550)];
    _editorRoll.accessibilityElement = YES;
    _editorRoll.accessibilityRole = NSAccessibilityGroupRole;
    _editorRoll.accessibilityLabel = @"MIDI候補差分表示";
    _editorRoll.accessibilityIdentifier = @"merlai.editor-roll";
    _editorRoll.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    [_editorRoll setEditable:NO target:nil action:nil];
    [_editorView addSubview:_editorRoll];
    _editorRevisedButton = [[MerlaiButton alloc] initWithFrame:NSZeroRect];
    _editorRevisedButton.title = @"修正案を聴く"; _editorRevisedButton.target = self;
    _editorRevisedButton.action = @selector(revised:);
    _editorRevisedButton.buttonType = NSButtonTypeToggle;
    _editorApplyButton = [[MerlaiButton alloc] initWithFrame:NSZeroRect];
    _editorApplyButton.title = @"候補を確定"; _editorApplyButton.target = self;
    _editorApplyButton.action = @selector(apply:);
    NSArray *editorButtons = @[
      [self editorButton:@"原案を聴く" action:@selector(original:)],
      [self editorButton:@"指示を修正" action:@selector(returnToInstruction:)],
      _editorRevisedButton, _editorApplyButton,
    ];
    NSArray<NSString *> *editorIDs = @[@"merlai.editor-copy", @"merlai.editor-undo",
      @"merlai.editor-audition", @"merlai.editor-confirm"];
    for (NSUInteger i = 0; i < editorButtons.count; ++i) {
      NSButton *button = editorButtons[i];
      button.frame = NSMakeRect(16 + i * 180, 28, 170, 32);
      button.bezelStyle = NSBezelStyleRounded;
      button.accessibilityIdentifier = editorIDs[i];
      [_editorView addSubview:button];
    }
    _editorRevisedButton.enabled = _editorApplyButton.enabled = NO;
    _auditioningRevised = NO; [self updateAuditionButtons];
    self.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    __weak MerlaiPhrasePanel *weak = self;
    _timer = [NSTimer scheduledTimerWithTimeInterval:.25 repeats:YES
      block:^(NSTimer *t) { [weak poll]; }];
    _timer.tolerance = .08;
    [self refreshProviders:nil];
  }
  return self;
}
- (void)changeTab:(NSSegmentedControl *)sender {
  BOOL editing = sender.selectedSegment == 1;
  _generationView.hidden = editing;
  _editorView.hidden = !editing;
  if (editing) [self.window makeFirstResponder:nil];
}
- (void)returnToInstruction:(id)sender {
  _tabs.selectedSegment = 0; [self changeTab:_tabs];
  [self.window makeFirstResponder:_instruction];
}
- (void)setExportEnabled:(BOOL)enabled confirmed:(BOOL)confirmed {
  _midiDragView.enabled = enabled;
  _midiDragView.confirmed = confirmed;
  _saveMIDIButton.enabled = _showMIDIButton.enabled = enabled;
  _apply.title = confirmed ? @"✓ 候補を確定済み" : @"候補を確定";
  _editorApplyButton.title = _apply.title;
  _editorApplyButton.enabled = _apply.enabled;
  _lastMIDIURL = nil;
}
- (void)updateAuditionButtons {
  _originalButton.state = _auditioningRevised ? NSControlStateValueOff : NSControlStateValueOn;
  _revisedButton.state = _auditioningRevised ? NSControlStateValueOn : NSControlStateValueOff;
  _editorRevisedButton.state = _revisedButton.state;
  _originalButton.title = _auditioningRevised ? @"原案を聴く" : @"✓ 原案を試聴中";
  _revisedButton.title = _auditioningRevised ? @"✓ 候補を試聴中" : @"候補を聴く";
  _editorRevisedButton.title = _revisedButton.title;
}
- (Phrase)exportPhrase { return _hasDraft ? _draft : _current; }
- (NSURL *)writeCandidateToURL:(NSURL *)url error:(NSError **)error {
  Phrase exportPhrase = [self exportPhrase];
  std::vector<uint8_t> bytes = merlai_midi_file(exportPhrase);
  NSData *data = [NSData dataWithBytes:bytes.data() length:bytes.size()];
  if (![data writeToURL:url options:NSDataWritingAtomic error:error]) return nil;
  _lastMIDIURL = url;
  return url;
}
- (NSURL *)midiDragURL {
  NSString *name = [NSString stringWithFormat:@"Merlai-%llu-candidate.mid",
    (unsigned long long)_instanceId];
  NSURL *url = [NSURL fileURLWithPath:[NSTemporaryDirectory() stringByAppendingPathComponent:name]];
  NSError *error = nil;
  if (![self writeCandidateToURL:url error:&error]) {
    _message.stringValue = [NSString stringWithFormat:@"MIDIを書き出せませんでした: %@",
      error.localizedDescription];
    return nil;
  }
  _message.stringValue = @"ドラッグ中です。Logicの目的トラック・目的小節へドロップしてください。";
  return url;
}
- (void)saveMIDI:(id)sender {
  NSSavePanel *panel = [NSSavePanel savePanel];
  panel.nameFieldStringValue = @"Merlai Candidate.mid";
  panel.allowedContentTypes = @[UTTypeMIDI];
  [panel beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse response) {
    if (response != NSModalResponseOK) return;
    NSError *error = nil;
    if ([self writeCandidateToURL:panel.URL error:&error])
      self->_message.stringValue = @"MIDIファイルを保存しました。";
    else
      self->_message.stringValue = [NSString stringWithFormat:@"MIDIを保存できませんでした: %@",
        error.localizedDescription];
  }];
}
- (void)showMIDI:(id)sender {
  NSURL *url = _lastMIDIURL ?: [self midiDragURL];
  if (url) [NSWorkspace.sharedWorkspace activateFileViewerSelectingURLs:@[url]];
}
- (void)beginManualEdit:(id)sender {
  if (!_loaded) { _message.stringValue = @"先にフレーズを取り込んでください。"; return; }
  _draft = _current; _hasDraft = true;
  [_roll setProposal:_draft visible:YES]; [_editorRoll setOriginal:_original];
  [_editorRoll setProposal:_draft visible:YES];
  _apply.enabled = _revisedButton.enabled = YES;
  _editorApplyButton.enabled = _editorRevisedButton.enabled = YES;
  [self setExportEnabled:YES confirmed:NO];
}
- (void)editorChanged:(MerlaiPianoRoll *)sender {
  _draft = [sender proposal]; _hasDraft = true;
  [_roll setProposal:_draft visible:YES]; _apply.enabled = _revisedButton.enabled = YES;
  _editorApplyButton.enabled = _editorRevisedButton.enabled = YES;
  [self setExportEnabled:YES confirmed:NO];
}
- (void)undoManualEdit:(id)sender { [_editorRoll undoCandidate]; }
- (void)dealloc { [_timer invalidate]; [_generationTimer invalidate]; [_modelTask terminate]; }
- (void)renameSource:(id)sender {
  merlai_link_rename(_instanceId, _sourceName.stringValue.UTF8String);
  _sourcesSignature = 0;
}
- (void)refreshSources {
#if defined(MERLAI_UI_TESTING)
  ++_testSourceRefreshes;
#endif
  LinkSourceInfo entries[64]{};
  size_t count = std::min<size_t>(merlai_link_list(_instanceId, entries, 64), 64);
  uint64_t signature = count;
  for (size_t i = 0; i < count; ++i)
    signature ^= entries[i].id * 1099511628211ULL ^ entries[i].revision;
  if (signature == _sourcesSignature) return;
  NSDictionary *selectedInfo = _sourcePopup.selectedItem.representedObject;
  uint64_t selected = [selectedInfo[@"id"] unsignedLongLongValue];
  [_sourcePopup removeAllItems];
  [_sourcePopup addItemWithTitle:@"入力元: このトラック"];
  _sourcePopup.lastItem.representedObject = nil;
  for (size_t i = 0; i < count; ++i) {
    NSString *name = [NSString stringWithUTF8String:entries[i].name];
    NSString *kind = entries[i].kind == 1 ? @"音声" : @"MIDI";
    [_sourcePopup addItemWithTitle:[NSString stringWithFormat:@"入力元: %@ [%@] (%u)", name, kind, entries[i].count]];
    _sourcePopup.lastItem.representedObject = @{@"id": @(entries[i].id), @"name": name,
      @"kind": kind, @"revision": @(entries[i].revision)};
    if (entries[i].id == selected) [_sourcePopup selectItem:_sourcePopup.lastItem];
  }
  _sourcesSignature = signature;
}
- (OSStatus)readCaptureInfo:(CaptureInfo *)info {
#if defined(MERLAI_UI_TESTING)
  if (_useTestCapture) { *info = _testCapture; return noErr; }
#endif
  UInt32 size = sizeof(*info);
  return AudioUnitGetProperty(_unit, CaptureProgress, 0, 0, info, &size);
}
- (OSStatus)readCapturedPhrase:(Phrase *)phrase {
#if defined(MERLAI_UI_TESTING)
  if (_useTestCapture) { *phrase = _testCapturedPhrase; return noErr; }
#endif
  UInt32 size = sizeof(*phrase);
  return AudioUnitGetProperty(_unit, ReadPhrase, 0, 0, phrase, &size);
}
- (void)poll {
  // Capture is independent from text entry. Keep progress and completion
  // flowing while an IME owns the first responder, but defer rebuilding the
  // source menu until editing ends.
  if (!MerlaiIsEditingTextInView(self)) [self refreshSources];
  CaptureInfo info{};
  if ([self readCaptureInfo:&info] != noErr) return;
  if (info.state == Capturing && info.end > info.start) {
    _progress.doubleValue = std::clamp(
      (info.position - info.start) / (info.end - info.start), 0., 1.);
    _captureSummary.stringValue = [NSString stringWithFormat:
      @"%@ → %@  •  取り込み中 %u音", BeatLabel(info.start),
      BeatLabel(info.end), info.count];
    _message.stringValue = @"取り込み中です。このままサイクル右端まで再生してください。";
  } else if (info.state == Armed) {
    _progress.doubleValue = 0;
    _captureSummary.stringValue = @"待機中 — 再生位置をサイクル先頭へ移動して再生";
  } else if (info.state == Ready && !_loaded) {
    if ([self readCapturedPhrase:&_original] == noErr) {
      UInt32 originalMode = 0;
      AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &originalMode, sizeof(originalMode));
      ++_generationRevision; _generateButton.enabled = YES; _hasDraft = false;
      _current = _original; _loaded = true; _progress.doubleValue = 1;
      _loadedSourceId = _instanceId; _loadedSourceRevision = 0;
      _loadedSourceName = _sourceName.stringValue; _loadedSourceKind = @"MIDI";
      _captureSummary.stringValue = [NSString stringWithFormat:
        @"%@ → %@  •  %u音を取り込み済み", BeatLabel(_original.start),
        BeatLabel(_original.end), _original.count];
      _activeSource.stringValue = [NSString stringWithFormat:@"使用中: %@ [MIDI]・%@・このトラック",
        _loadedSourceName, PhraseSummary(_original)];
      [_roll setOriginal:_original]; [_roll setProposal:_original visible:NO];
      [_editorRoll setOriginal:_original]; [_editorRoll setProposal:_original visible:NO];
      merlai_link_rename(_instanceId, _sourceName.stringValue.UTF8String);
      merlai_link_publish(_instanceId, _original);
      _sourcesSignature = 0;
      _plan.enabled = _originalButton.enabled = YES;
      _revisedButton.enabled = _undoButton.enabled = _apply.enabled = NO;
      _editorRevisedButton.enabled = _editorApplyButton.enabled = NO;
      [self setExportEnabled:NO confirmed:NO];
      _auditioningRevised = NO; [self updateAuditionButtons];
      _message.stringValue =
        @"取り込み完了。青い原案を確認し、変更指示を書いて「変更内容を確認」を押してください。";
    }
  } else if (info.state == Failed) {
    _progress.doubleValue = 0;
    _captureSummary.stringValue = @"取り込み失敗 — ノートを含むサイクルを確認";
    _message.stringValue =
      @"サイクル範囲とリージョン内のノートを確認し、もう一度取り込んでください。";
  }
}
- (void)loadSource:(id)sender {
  NSDictionary *represented = _sourcePopup.selectedItem.representedObject;
  uint64_t source = [represented[@"id"] unsignedLongLongValue];
  if (!source) {
    _message.stringValue = @"このトラックでは「フレーズを取り込む」を使ってください。";
    return;
  }
  uint64_t revision = 0;
  Phrase linked{};
  if (!merlai_link_read(source, linked, revision)) {
    _message.stringValue = @"入力元を読み込めませんでした。入力元で取り込みを完了してください。";
    return;
  }
  UInt32 originalMode = 0;
  AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &originalMode, sizeof(originalMode));
  ++_generationRevision; _generateButton.enabled = YES; _hasDraft = false;
  _original = _current = linked; _loaded = true; _undo.clear();
  _loadedSourceId = source; _loadedSourceRevision = revision;
  _loadedSourceName = represented[@"name"] ?: @"別トラック";
  _loadedSourceKind = represented[@"kind"] ?: @"MIDI";
  [_roll setOriginal:_original]; [_roll setProposal:_original visible:NO];
  [_editorRoll setOriginal:_original]; [_editorRoll setProposal:_original visible:NO];
  _progress.doubleValue = 1;
  _captureSummary.stringValue = [NSString stringWithFormat:@"%@ → %@  •  別トラックから%u音",
    BeatLabel(linked.start), BeatLabel(linked.end), linked.count];
  _activeSource.stringValue = [NSString stringWithFormat:@"使用中: %@ [%@]・%@・rev %llu",
    _loadedSourceName, _loadedSourceKind, PhraseSummary(linked),
    (unsigned long long)_loadedSourceRevision];
  _plan.enabled = _originalButton.enabled = YES;
  _revisedButton.enabled = _undoButton.enabled = _apply.enabled = NO;
  _editorRevisedButton.enabled = _editorApplyButton.enabled = NO;
  [self setExportEnabled:NO confirmed:NO];
  _auditioningRevised = NO; [self updateAuditionButtons];
  _message.stringValue = @"別トラックの入力を読み込みました。生成目的を選び「候補を生成」を押してください。";
}
- (void)arm:(id)sender {
  UInt32 value = 1;
  if (AudioUnitSetProperty(_unit, Arm, 0, 0, &value, sizeof(value)) == noErr) {
    ++_generationRevision; _generateButton.enabled = YES;
    _loaded = false; _hasDraft = false; _undo.clear(); [_roll clear]; [_editorRoll clear];
    _loadedSourceId = _loadedSourceRevision = 0; _loadedSourceName = nil; _loadedSourceKind = nil;
    _activeSource.stringValue = @"使用中: 取り込み待機中";
    _apply.enabled = _plan.enabled = _originalButton.enabled =
      _revisedButton.enabled = _undoButton.enabled = NO;
    _editorRevisedButton.enabled = _editorApplyButton.enabled = NO;
    [self setExportEnabled:NO confirmed:NO];
    _auditioningRevised = NO; [self updateAuditionButtons];
    _captureSummary.stringValue = @"待機中 — 再生位置をサイクル先頭へ移動して再生";
    _message.stringValue = @"取り込み待機中です。Logicをサイクル先頭から再生してください。";
  }
}
- (void)setMode:(BOOL)revised {
  UInt32 value = revised;
  AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &value, sizeof(value));
  _auditioningRevised = revised;
  [self updateAuditionButtons];
  _message.stringValue = revised
    ? @"修正案を選択中。次のサイクル先頭から切り替わります。"
    : @"原案を選択中。次のサイクル先頭から切り替わります。";
}
- (void)original:(id)sender { [self setMode:NO]; }
- (void)revised:(id)sender {
  if (_loaded && _hasDraft && [self submit:_draft]) [self setMode:YES];
  else if (_loaded && !_undo.empty() && [self submit:_current]) [self setMode:YES];
}
- (void)plan:(id)sender {
  UInt32 originalMode = 0;
  AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &originalMode, sizeof(originalMode));
  _apply.enabled = _revisedButton.enabled = NO; _hasDraft = false;
  _editorApplyButton.enabled = _editorRevisedButton.enabled = NO;
  [self setExportEnabled:NO confirmed:NO];
  if (!_loaded) { _message.stringValue = @"先に原案を取り込んでください。"; return; }
  _draft = _current;
  int n = merlai_edit(_current.notes.data(), _current.count,
    _current.end - _current.start, _instruction.string.UTF8String,
    _draft.notes.data());
  if (n < 0) {
    _message.stringValue =
      @"指示を解釈できませんでした。「後半だけ半分に」「休符を増やして」などを試してください。";
    [_roll setProposal:_current visible:NO]; return;
  }
  _draft.count = n; [_roll setProposal:_draft visible:YES];
  [_editorRoll setOriginal:_original]; [_editorRoll setProposal:_draft visible:YES];
  _message.stringValue = [NSString stringWithFormat:
    @"プレビュー: 青 %u音 → オレンジ %d音。よければ候補を確定してください。",
    _current.count, n];
  _hasDraft = true; _apply.enabled = _revisedButton.enabled = YES;
  _editorApplyButton.enabled = _editorRevisedButton.enabled = YES;
}
- (NSString *)bridgePath {
  CFBundleRef bundle = CFBundleGetBundleWithIdentifier(
    CFSTR("io.github.yoshitake945.Merlai.MidiFX"));
  NSURL *url = bundle ? CFBridgingRelease(CFBundleCopyExecutableURL(bundle)) : nil;
  return url ? [[url URLByDeletingLastPathComponent].path
    stringByAppendingPathComponent:@"ModelBridge"] : @"";
}
- (NSData *)runBridge:(NSArray<NSString *> *)arguments input:(NSData *)input
                error:(NSString **)error {
  NSString *path = [self bridgePath];
  if (![[NSFileManager defaultManager] isExecutableFileAtPath:path]) {
    if (error) *error = @"ModelBridgeが見つかりません。MIDI FXを再ビルドしてください。";
    return nil;
  }
  NSTask *task = [[NSTask alloc] init];
  task.executableURL = [NSURL fileURLWithPath:path]; task.arguments = arguments;
  NSPipe *inPipe = [NSPipe pipe], *outPipe = [NSPipe pipe], *errPipe = [NSPipe pipe];
  task.standardInput = inPipe; task.standardOutput = outPipe; task.standardError = errPipe;
  NSError *launchError = nil;
  if (![task launchAndReturnError:&launchError]) {
    if (error) *error = launchError.localizedDescription; return nil;
  }
  if (input.length) [inPipe.fileHandleForWriting writeData:input];
  [inPipe.fileHandleForWriting closeFile];
  NSData *result = [outPipe.fileHandleForReading readDataToEndOfFile];
  [task waitUntilExit];
  if (task.terminationStatus != 0) {
    NSData *diagnostic = [errPipe.fileHandleForReading readDataToEndOfFile];
    if (error) *error = [[NSString alloc] initWithData:diagnostic
      encoding:NSUTF8StringEncoding] ?: @"ModelBridgeが停止しました。";
    return nil;
  }
  return result;
}
- (void)setGenerationStage:(NSString *)stage message:(NSString *)message {
  _generationStage = message.length ? message : stage;
  if (!_generationStarted) _generationStarted = [NSDate date];
  NSTimeInterval elapsed = -[_generationStarted timeIntervalSinceNow];
  _message.stringValue = [NSString stringWithFormat:@"%@（%.1f秒）", _generationStage, elapsed];
}
- (void)startGenerationProgress {
  _generationStarted = [NSDate date]; _generationStage = @"MIDIと指示を準備しています";
  _cancelButton.hidden = NO; _builtinButton.hidden = YES;
  [_generationTimer invalidate];
  __weak MerlaiPhrasePanel *weakSelf = self;
  _generationTimer = [NSTimer scheduledTimerWithTimeInterval:.25 repeats:YES block:^(NSTimer *timer) {
    MerlaiPhrasePanel *panel = weakSelf;
    if (panel && panel->_generationStarted)
      [panel setGenerationStage:@"generating" message:panel->_generationStage];
  }];
}
- (void)stopGenerationProgress {
  [_generationTimer invalidate]; _generationTimer = nil; _generationStarted = nil;
  _cancelButton.hidden = YES; _modelTask = nil;
}
- (void)cancelGeneration:(id)sender {
  ++_generationRevision;
  [_modelTask terminate]; [self stopGenerationProgress];
  _generateButton.enabled = _plan.enabled = YES;
  _message.stringValue = @"生成を中止しました。既存の候補は変更していません。";
  _assistantMessage.string = @"生成を中止しました。";
}
- (NSDictionary *)runBridgeStreaming:(NSDictionary *)request error:(NSString **)error {
  NSString *path = [self bridgePath];
  if (![[NSFileManager defaultManager] isExecutableFileAtPath:path]) {
    if (error) *error = @"ModelBridgeが見つかりません。"; return nil;
  }
  NSTask *task = [[NSTask alloc] init]; task.executableURL = [NSURL fileURLWithPath:path];
  task.arguments = @[@"generate-stream"];
  NSPipe *inPipe = [NSPipe pipe], *outPipe = [NSPipe pipe], *errPipe = [NSPipe pipe];
  task.standardInput = inPipe; task.standardOutput = outPipe; task.standardError = errPipe;
  NSError *launchError = nil;
  if (![task launchAndReturnError:&launchError]) {
    if (error) *error = launchError.localizedDescription; return nil;
  }
  dispatch_async(dispatch_get_main_queue(), ^{ self->_modelTask = task; });
  NSData *body = [NSJSONSerialization dataWithJSONObject:request options:0 error:nil];
  [inPipe.fileHandleForWriting writeData:body]; [inPipe.fileHandleForWriting closeFile];
  NSMutableData *buffer = [NSMutableData data]; NSDictionary *result = nil;
  while (true) {
    NSData *chunk = [outPipe.fileHandleForReading availableData];
    if (!chunk.length) break;
    [buffer appendData:chunk];
    while (true) {
      const uint8_t *bytes = (const uint8_t *)buffer.bytes;
      NSUInteger newline = NSNotFound;
      for (NSUInteger i = 0; i < buffer.length; ++i) if (bytes[i] == '\n') { newline = i; break; }
      if (newline == NSNotFound) break;
      NSData *line = [buffer subdataWithRange:NSMakeRange(0, newline)];
      [buffer replaceBytesInRange:NSMakeRange(0, newline + 1) withBytes:nullptr length:0];
      NSDictionary *event = [NSJSONSerialization JSONObjectWithData:line options:0 error:nil];
      if ([event[@"type"] isEqual:@"status"]) {
        NSString *stage = event[@"stage"] ?: @"generating";
        NSString *message = event[@"message"] ?: @"生成中";
        dispatch_async(dispatch_get_main_queue(), ^{ [self setGenerationStage:stage message:message]; });
      } else if ([event[@"type"] isEqual:@"result"]) result = event[@"result"];
      else if ([event[@"type"] isEqual:@"error"] && error) *error = event[@"message"];
    }
  }
  [task waitUntilExit];
  if (!result && error && !*error) {
    NSData *diagnostic = [errPipe.fileHandleForReading readDataToEndOfFile];
    *error = [[NSString alloc] initWithData:diagnostic encoding:NSUTF8StringEncoding]
      ?: @"モデル応答を読み取れませんでした。";
  }
  return result;
}
- (void)refreshProviders:(id)sender {
  NSString *endpoint = _endpointField.stringValue;
  [[NSUserDefaults standardUserDefaults] setObject:endpoint forKey:@"MerlaiModelEndpoint"];
  _providerPopup.enabled = NO;
  __weak MerlaiPhrasePanel *weakSelf = self;
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
    NSString *error = nil;
    NSMutableArray *arguments = [NSMutableArray arrayWithObject:@"providers"];
    if (endpoint.length) [arguments addObject:endpoint];
    NSData *data = [weakSelf runBridge:arguments input:nil error:&error];
    NSArray *providers = data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
    dispatch_async(dispatch_get_main_queue(), ^{
      MerlaiPhrasePanel *panel = weakSelf; if (!panel) return;
      panel->_providers = [providers isKindOfClass:NSArray.class] ? providers : @[];
      [panel->_providerPopup removeAllItems];
      [panel->_providerPopup addItemWithTitle:@"内蔵ルール"];
      for (NSDictionary *provider in panel->_providers) {
        NSString *state = [provider[@"available"] boolValue] ? @"" : @"（利用不可）";
        NSString *location = [provider[@"locality"] isEqual:@"local"] ? @"ローカル" : @"クラウド";
        [panel->_providerPopup addItemWithTitle:[NSString stringWithFormat:@"%@ [%@]%@",
          provider[@"displayName"], location, state]];
        panel->_providerPopup.lastItem.representedObject = provider;
      }
      panel->_providerPopup.enabled = YES;
      [panel providerChanged:nil];
      if (error.length) panel->_message.stringValue = error;
    });
  });
}
- (void)providerChanged:(id)sender {
  [_modelPopup removeAllItems];
  NSDictionary *provider = _providerPopup.selectedItem.representedObject;
  if (!provider) { [_modelPopup addItemWithTitle:@"自動"]; _modelPopup.enabled = NO; return; }
  NSArray *models = provider[@"models"];
  if (models.count) {
    for (NSDictionary *model in models) {
      [_modelPopup addItemWithTitle:model[@"displayName"] ?: model[@"id"]];
      _modelPopup.lastItem.representedObject = model[@"id"];
    }
  } else {
    [_modelPopup addItemWithTitle:@"既定モデル"];
    _modelPopup.lastItem.representedObject = @"";
  }
  _modelPopup.enabled = [provider[@"available"] boolValue];
  _message.stringValue = provider[@"detail"] ?: @"モデル提供元を選択しました。";
}
- (NSDictionary *)generationRequestFor:(const Phrase &)input
                                purpose:(uint32_t)purpose {
  NSMutableArray *notes = [NSMutableArray arrayWithCapacity:input.count];
  for (uint32_t i = 0; i < input.count; ++i) {
    const Note &n = input.notes[i];
    [notes addObject:@{@"start": @(n.start), @"end": @(n.end), @"pitch": @(n.pitch),
      @"velocity": @(n.velocity), @"channel": @(n.channel)}];
  }
  NSDictionary *provider = _providerPopup.selectedItem.representedObject;
  NSString *model = _modelPopup.selectedItem.representedObject ?: @"";
  NSString *source = [NSString stringWithFormat:@"%@ [%@]・%@・rev %llu",
    _loadedSourceName ?: @"このトラック", _loadedSourceKind ?: @"MIDI",
    PhraseSummary(input), (unsigned long long)_loadedSourceRevision];
  MusicalContext context{}; UInt32 contextSize = sizeof(context);
  AudioUnitGetProperty(_unit, CurrentMusicalContext, 0, 0, &context, &contextSize);
  NSString *timeSignature = [NSString stringWithFormat:@"%g/%u",
    context.numerator, context.denominator];
  NSDictionary *keyScale = _keyScalePopup.selectedItem.representedObject;
  double sourceSpan = input.end - input.start;
  double targetSpan = purpose == 4 ? sourceSpan * 2 : sourceSpan;
  return @{
    @"providerId": provider[@"id"] ?: @"",
    @"model": model,
    @"endpoint": _endpointField.stringValue ?: @"",
    @"payload": @{
      @"version": @2,
      @"instruction": _instruction.string ?: @"",
      @"purpose": @[@"edit", @"bass", @"chords", @"counter_melody", @"continue"][purpose],
      @"musicalContext": @{@"span": @(targetSpan),
        @"tempo": context.tempo > 0 ? @(context.tempo) : [NSNull null],
        @"timeSignature": timeSignature, @"source": source,
        @"sourceId": @(_loadedSourceId), @"sourceRevision": @(_loadedSourceRevision),
        @"sourceKind": _loadedSourceKind ?: @"MIDI"},
      @"notes": notes, @"contexts": @[@{@"role": @"melody", @"notes": notes,
        @"sourceId": @(_loadedSourceId), @"sourceRevision": @(_loadedSourceRevision)}],
      @"keyRoot": keyScale[@"root"] ?: [NSNull null],
      @"scale": keyScale[@"scale"] ?: @0,
      @"targetSpan": @(targetSpan), @"variation": @1,
    }
  };
}
- (int)generateWithBridge:(NSDictionary *)request output:(Phrase &)output
                    error:(NSString **)error response:(NSDictionary **)fullResponse {
  NSDictionary *response = [self runBridgeStreaming:request error:error];
  if (fullResponse) *fullResponse = response;
  NSArray *notes = response[@"notes"];
  if (![notes isKindOfClass:NSArray.class] || !notes.count || notes.count > Capacity) return -1;
  double span = output.end - output.start;
  for (NSUInteger i = 0; i < notes.count; ++i) {
    NSDictionary *value = notes[i];
    Note note{[value[@"start"] doubleValue], [value[@"end"] doubleValue],
      (uint8_t)[value[@"pitch"] unsignedIntValue], (uint8_t)[value[@"velocity"] unsignedIntValue],
      (uint8_t)[value[@"channel"] unsignedIntValue]};
    if (!std::isfinite(note.start) || !std::isfinite(note.end) || note.start < 0 ||
        note.end <= note.start || note.end > span || [value[@"pitch"] unsignedIntValue] > 127 ||
        [value[@"velocity"] unsignedIntValue] > 127 || [value[@"channel"] unsignedIntValue] > 15)
      return -1;
    output.notes[i] = note;
  }
  return (int)notes.count;
}
- (void)showAssistantResponse:(NSDictionary *)response {
  _assistantMessage.string = response[@"message"] ?: @"モデルから説明はありませんでした。";
  _suggestions = [response[@"suggestions"] isKindOfClass:NSArray.class] ? response[@"suggestions"] : @[];
  NSUInteger count = std::min<NSUInteger>(3, _suggestions.count);
  for (NSUInteger i = 0; i < _suggestionButtons.count; ++i) {
    MerlaiButton *button = _suggestionButtons[i];
    button.hidden = i >= count;
    if (i < count) button.title = _suggestions[i];
  }
}
- (void)useSuggestion:(NSButton *)sender {
  NSUInteger index = sender.tag - 7100;
  if (index >= _suggestions.count) return;
  _instruction.string = _suggestions[index];
  [self.window makeFirstResponder:_instruction];
}
- (void)generateBuiltin:(id)sender {
  _forceBuiltinOnce = true;
  [self generate:sender];
}
- (void)generate:(id)sender {
  UInt32 originalMode = 0;
  AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &originalMode, sizeof(originalMode));
  _apply.enabled = _revisedButton.enabled = NO; _hasDraft = false;
  _editorApplyButton.enabled = _editorRevisedButton.enabled = NO;
  [self setExportEnabled:NO confirmed:NO];
  _assistantMessage.string = @"モデルの応答を待っています…";
  _suggestions = @[];
  for (NSButton *button in _suggestionButtons) button.hidden = YES;
  if (!_loaded) {
    _message.stringValue = @"先にこのトラックを取り込むか、別トラックの入力を読み込んでください。";
    return;
  }
  uint32_t purpose = (uint32_t)_purposePopup.indexOfSelectedItem;
  Phrase input = purpose == 0 ? _current : _original;
  auto draft = std::make_shared<Phrase>(_current);
  double sourceSpan = input.end - input.start;
  if (purpose == 4) draft->end = draft->start + sourceSpan * 2;
  BOOL forceBuiltin = _forceBuiltinOnce; _forceBuiltinOnce = false;
  NSDictionary *provider = forceBuiltin ? nil : _providerPopup.selectedItem.representedObject;
  NSString *instruction = [_instruction.string copy];
  NSDictionary *keyScale = _keyScalePopup.selectedItem.representedObject;
  uint32_t keyRoot = keyScale ? [keyScale[@"root"] unsignedIntValue] : 255;
  uint32_t scale = [keyScale[@"scale"] unsignedIntValue];
  if (provider && ![provider[@"available"] boolValue]) {
    _message.stringValue = provider[@"detail"] ?: @"選択したモデルは利用できません。"; return;
  }
  if ([provider[@"locality"] isEqual:@"cloud"]) {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"構造化MIDIをクラウドLLMへ送信しますか？";
    alert.informativeText = @"指示、生成目的、範囲、拍子、入力元表示名、MIDIノートを送ります。音声とLogicプロジェクトは送りません。";
    [alert addButtonWithTitle:@"送信して生成"]; [alert addButtonWithTitle:@"キャンセル"];
    if ([alert runModal] != NSAlertFirstButtonReturn) return;
  }
  NSDictionary *request = provider ? [self generationRequestFor:input purpose:purpose] : nil;
  uint64_t revision = ++_generationRevision;
  _generateButton.enabled = _plan.enabled = NO;
  _builtinButton.hidden = YES;
  if (request) [self startGenerationProgress];
  else _message.stringValue = @"内蔵ルールで候補を生成しています。";
  __weak MerlaiPhrasePanel *weakSelf = self;
  dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
    NSString *bridgeError = nil;
    NSDictionary *modelResponse = nil;
    int n = request ? [weakSelf generateWithBridge:request output:*draft error:&bridgeError
                                          response:&modelResponse] : -1;
    if (!request) {
      if (purpose == 0) n = merlai_edit(input.notes.data(), input.count,
        input.end - input.start, instruction.UTF8String,
        draft->notes.data());
      else {
        n = merlai_generate_context(input.notes.data(), input.count, nullptr, 0,
          sourceSpan, purpose, purpose == 4 ? sourceSpan * 2 : sourceSpan,
          keyRoot, scale, 1, draft->notes.data());
      }
    }
    draft->count = n < 0 ? 0 : (uint32_t)n;
    dispatch_async(dispatch_get_main_queue(), ^{
      MerlaiPhrasePanel *panel = weakSelf;
      if (!panel || revision != panel->_generationRevision) return;
      if (request) [panel stopGenerationProgress];
      panel->_generateButton.enabled = panel->_plan.enabled = YES;
      if (n < 0) {
        panel->_assistantMessage.string = bridgeError.length
          ? [NSString stringWithFormat:@"生成できませんでした: %@", bridgeError]
          : @"候補を生成できませんでした。指示を変更して再試行してください。";
        if (request) {
          panel->_message.stringValue = [NSString stringWithFormat:
            @"モデル生成に失敗しました: %@ 「候補を生成」で再試行できます。",
            bridgeError ?: @"応答を読み取れませんでした。"];
          panel->_builtinButton.hidden = NO;
        } else {
          panel->_message.stringValue = purpose == 0
            ? @"内蔵編集ではこの指示を解釈できませんでした。LLMを選ぶか指示を変更してください。"
            : @"この入力から内蔵候補を生成できませんでした。";
        }
        return;
      }
      panel->_draft = *draft;
      panel->_hasDraft = true;
      [panel setExportEnabled:YES confirmed:NO];
      [panel->_roll setProposal:panel->_draft visible:YES];
      [panel->_editorRoll setOriginal:panel->_original];
      [panel->_editorRoll setProposal:panel->_draft visible:YES];
      NSString *purposeName = @[@"編集", @"ベース", @"コード", @"対旋律", @"続き"][purpose];
      panel->_message.stringValue = [NSString stringWithFormat:
        @"%@候補: 青 %u音 → オレンジ %d音。適用前のプレビューです。",
        purposeName, input.count, n];
      panel->_builtinButton.hidden = YES;
      if (modelResponse) [panel showAssistantResponse:modelResponse];
      else panel->_assistantMessage.string = @"内蔵ルールで候補を生成しました。必要に応じてMIDI編集で調整できます。";
      panel->_apply.enabled = panel->_revisedButton.enabled = YES;
      panel->_editorApplyButton.enabled = panel->_editorRevisedButton.enabled = YES;
    });
  });
}
- (BOOL)submit:(const Phrase &)p {
  if (AudioUnitSetProperty(_unit, Submit, 0, 0, &p, sizeof(p)) != noErr) {
    _message.stringValue =
      @"反映待ちです。サイクル再生を続けてからもう一度お試しください。";
    return NO;
  }
  return YES;
}
- (void)apply:(id)sender {
  if (!_hasDraft) return;
  if (![self submit:_draft]) return;
  _undo.push_back(_current); _current = _draft; _hasDraft = false; _apply.enabled = NO;
  _revisedButton.enabled = _undoButton.enabled = YES;
  _editorApplyButton.enabled = NO; _editorRevisedButton.enabled = YES;
  [self setExportEnabled:YES confirmed:YES];
  [_roll setProposal:_current visible:YES]; [_editorRoll setProposal:_current visible:YES];
  [self setMode:YES];
}
- (void)undoEdit:(id)sender {
  if (_undo.empty() || ![self submit:_undo.back()]) return;
  _current = _undo.back(); _undo.pop_back(); _apply.enabled = NO;
  _hasDraft = false;
  _undoButton.enabled = _revisedButton.enabled = !_undo.empty();
  _editorRevisedButton.enabled = _revisedButton.enabled;
  [_roll setProposal:_current visible:!_undo.empty()];
  [_editorRoll setProposal:_current visible:!_undo.empty()];
  [self setExportEnabled:YES confirmed:YES];
  [self setMode:!_undo.empty()];
}
#if defined(MERLAI_UI_TESTING)
- (void)loadPhraseForTesting:(const Phrase &)phrase {
  _original = _current = phrase; _loaded = true; _hasDraft = false; _undo.clear();
  [_roll setOriginal:phrase]; [_editorRoll setOriginal:phrase];
  _plan.enabled = _originalButton.enabled = YES;
}
- (uint32_t)draftCountForTesting { return _hasDraft ? _draft.count : 0; }
- (BOOL)isEditingTextForTesting { return MerlaiIsEditingTextInView(self); }
- (void)setCaptureInfoForTesting:(const CaptureInfo &)info phrase:(const Phrase &)phrase {
  _useTestCapture = YES; _testCapture = info; _testCapturedPhrase = phrase;
}
- (void)pollForTesting { [self poll]; }
- (BOOL)isLoadedForTesting { return _loaded; }
- (NSUInteger)sourceRefreshesForTesting { return _testSourceRefreshes; }
- (void)setCandidateForTesting:(const Phrase &)phrase {
  _draft = phrase; _hasDraft = true;
  [self setExportEnabled:YES confirmed:NO];
}
- (Phrase)exportPhraseForTesting { return [self exportPhrase]; }
- (NSURL *)midiDragURLForTesting { return [self midiDragURL]; }
- (id<NSPasteboardWriting>)dragPasteboardWriterForTesting {
  return [_midiDragView dragPasteboardWriter];
}
- (void)showAssistantResponseForTesting:(NSDictionary *)response {
  [self showAssistantResponse:response];
}
#endif
@end

#if defined(MERLAI_UI_TESTING)
extern "C" NSView *merlai_ui_test_create(void) {
  return [[MerlaiPhrasePanel alloc] initWithUnit:nullptr];
}
extern "C" void merlai_ui_test_load_phrase(NSView *view, const Phrase *phrase) {
  [(MerlaiPhrasePanel *)view loadPhraseForTesting:*phrase];
}
extern "C" uint32_t merlai_ui_test_draft_count(NSView *view) {
  return [(MerlaiPhrasePanel *)view draftCountForTesting];
}
extern "C" BOOL merlai_ui_test_is_editing_text(NSView *view) {
  return [(MerlaiPhrasePanel *)view isEditingTextForTesting];
}
extern "C" void merlai_ui_test_set_capture(NSView *view, const CaptureInfo *info,
                                             const Phrase *phrase) {
  [(MerlaiPhrasePanel *)view setCaptureInfoForTesting:*info phrase:*phrase];
}
extern "C" void merlai_ui_test_poll(NSView *view) {
  [(MerlaiPhrasePanel *)view pollForTesting];
}
extern "C" BOOL merlai_ui_test_is_loaded(NSView *view) {
  return [(MerlaiPhrasePanel *)view isLoadedForTesting];
}
extern "C" NSUInteger merlai_ui_test_source_refreshes(NSView *view) {
  return [(MerlaiPhrasePanel *)view sourceRefreshesForTesting];
}
extern "C" void merlai_ui_test_set_candidate(NSView *view, const Phrase *phrase) {
  [(MerlaiPhrasePanel *)view setCandidateForTesting:*phrase];
}
extern "C" void merlai_ui_test_export_phrase(NSView *view, Phrase *phrase) {
  *phrase = [(MerlaiPhrasePanel *)view exportPhraseForTesting];
}
extern "C" NSURL *merlai_ui_test_drag_url(NSView *view) {
  return [(MerlaiPhrasePanel *)view midiDragURLForTesting];
}
extern "C" id<NSPasteboardWriting> merlai_ui_test_drag_writer(NSView *view) {
  return [(MerlaiPhrasePanel *)view dragPasteboardWriterForTesting];
}
extern "C" void merlai_ui_test_show_response(NSView *view, NSDictionary *response) {
  [(MerlaiPhrasePanel *)view showAssistantResponseForTesting:response];
}
#endif

@interface MerlaiPhraseViewFactory : NSObject <AUCocoaUIBase>
@end
@implementation MerlaiPhraseViewFactory
- (unsigned)interfaceVersion { return 0; }
- (NSView *)uiViewForAudioUnit:(AudioUnit)unit withSize:(NSSize)size {
  return [[MerlaiPhrasePanel alloc] initWithUnit:unit];
}
@end
