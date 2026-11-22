#include "Phrase.h"
#import <AudioUnit/AUCocoaUIView.h>
#import <Cocoa/Cocoa.h>
#include <algorithm>
#include <cmath>
#include <vector>

static NSString *BeatLabel(double beat) {
  NSInteger bar = (NSInteger)floor(beat / 4.0) + 1;
  NSInteger within = (NSInteger)floor(fmod(std::max(0.0, beat), 4.0)) + 1;
  return [NSString stringWithFormat:@"%ld.%ld", (long)bar, (long)within];
}

@interface MerlaiPianoRoll : NSView {
  Phrase _original, _proposal;
  BOOL _hasOriginal, _hasProposal;
}
- (void)setOriginal:(const Phrase &)p;
- (void)setProposal:(const Phrase &)p visible:(BOOL)visible;
- (void)clear;
@end

@implementation MerlaiPianoRoll
- (BOOL)isFlipped { return YES; }
- (void)setOriginal:(const Phrase &)p {
  _original = p; _hasOriginal = YES; [self setNeedsDisplay:YES];
}
- (void)setProposal:(const Phrase &)p visible:(BOOL)visible {
  _proposal = p; _hasProposal = visible; [self setNeedsDisplay:YES];
}
- (void)clear {
  _hasOriginal = _hasProposal = NO; [self setNeedsDisplay:YES];
}
- (void)drawPhrase:(const Phrase &)p rect:(NSRect)r color:(NSColor *)color {
  if (!p.count || p.end <= p.start) return;
  uint8_t low = 127, high = 0;
  for (uint32_t i = 0; i < p.count; ++i) {
    low = std::min(low, p.notes[i].pitch);
    high = std::max(high, p.notes[i].pitch);
  }
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
  if (_hasOriginal)
    [self drawPhrase:_original rect:top
               color:[NSColor colorWithRed:.30 green:.68 blue:1 alpha:1]];
  if (_hasProposal)
    [self drawPhrase:_proposal rect:bottom
               color:[NSColor colorWithRed:1 green:.55 blue:.28 alpha:1]];
  else {
    NSDictionary *empty = @{NSFontAttributeName: [NSFont systemFontOfSize:11],
      NSForegroundColorAttributeName: [NSColor colorWithWhite:.55 alpha:1]};
    [@"指示を確認すると表示されます"
        drawAtPoint:NSMakePoint(bottom.origin.x + 10, bottom.origin.y + 9)
      withAttributes:empty];
  }
}
@end

@interface MerlaiPhrasePanel : NSView {
  AudioUnit _unit;
  Phrase _original, _current, _draft;
  std::vector<Phrase> _undo;
  NSTextField *_instruction, *_message, *_captureSummary;
  NSButton *_plan, *_apply, *_originalButton, *_revisedButton, *_undoButton;
  NSProgressIndicator *_progress;
  MerlaiPianoRoll *_roll;
  NSTimer *_timer;
  bool _loaded;
}
- (instancetype)initWithUnit:(AudioUnit)unit;
@end

@implementation MerlaiPhrasePanel
- (NSButton *)button:(NSString *)title action:(SEL)action frame:(NSRect)frame {
  NSButton *b = [NSButton buttonWithTitle:title target:self action:action];
  b.frame = frame; b.bezelStyle = NSBezelStyleRounded; [self addSubview:b];
  return b;
}
- (NSTextField *)label:(NSString *)text frame:(NSRect)frame
                  size:(CGFloat)size bold:(BOOL)bold {
  NSTextField *l = [NSTextField labelWithString:text];
  l.frame = frame;
  l.font = [NSFont systemFontOfSize:size
                            weight:(bold ? NSFontWeightSemibold : NSFontWeightRegular)];
  l.textColor = [NSColor colorWithWhite:.82 alpha:1];
  [self addSubview:l]; return l;
}
- (instancetype)initWithUnit:(AudioUnit)unit {
  if ((self = [super initWithFrame:NSMakeRect(0, 0, 720, 470)])) {
    self.wantsLayer = YES;
    self.layer.backgroundColor = [NSColor colorWithWhite:.13 alpha:1].CGColor;
    _unit = unit;
    [self label:@"Merlai フレーズ編集" frame:NSMakeRect(16, 438, 220, 24) size:17 bold:YES];
    [self label:@"1  サイクル指定" frame:NSMakeRect(240, 440, 105, 20) size:12 bold:YES];
    [self label:@"2  取り込む" frame:NSMakeRect(350, 440, 90, 20) size:12 bold:YES];
    [self label:@"3  指示を確認" frame:NSMakeRect(445, 440, 105, 20) size:12 bold:YES];
    [self label:@"4  比較" frame:NSMakeRect(560, 440, 70, 20) size:12 bold:YES];
    [self button:@"2  フレーズを取り込む" action:@selector(arm:)
           frame:NSMakeRect(16, 393, 185, 32)];
    _captureSummary = [self label:@"未取り込み — Logicで先にサイクルを指定"
                            frame:NSMakeRect(216, 400, 480, 20) size:12 bold:NO];
    _progress = [[NSProgressIndicator alloc] initWithFrame:NSMakeRect(216, 389, 480, 8)];
    _progress.minValue = 0; _progress.maxValue = 1; _progress.indeterminate = NO;
    [self addSubview:_progress];
    _roll = [[MerlaiPianoRoll alloc] initWithFrame:NSMakeRect(16, 214, 680, 160)];
    _roll.wantsLayer = YES; _roll.layer.cornerRadius = 5;
    _roll.layer.masksToBounds = YES; [self addSubview:_roll];
    [self label:@"3  どう変えますか？" frame:NSMakeRect(16, 180, 170, 22) size:13 bold:YES];
    _instruction = [[NSTextField alloc] initWithFrame:NSMakeRect(16, 143, 495, 30)];
    _instruction.stringValue = @"後半だけ音数を半分に。最後の音は残して";
    [self addSubview:_instruction];
    _plan = [self button:@"変更内容を確認" action:@selector(plan:)
                   frame:NSMakeRect(520, 143, 176, 30)];
    _originalButton = [self button:@"原案を聴く" action:@selector(original:)
                             frame:NSMakeRect(16, 98, 112, 30)];
    _revisedButton = [self button:@"修正案を聴く" action:@selector(revised:)
                            frame:NSMakeRect(136, 98, 120, 30)];
    _apply = [self button:@"適用して修正案を聴く" action:@selector(apply:)
                    frame:NSMakeRect(264, 98, 190, 30)];
    _undoButton = [self button:@"一手戻す" action:@selector(undoEdit:)
                         frame:NSMakeRect(462, 98, 100, 30)];
    _apply.enabled = _plan.enabled = _originalButton.enabled =
        _revisedButton.enabled = _undoButton.enabled = NO;
    _message = [NSTextField wrappingLabelWithString:
      @"操作: ① Logicで黄色いサイクル範囲を指定  ② 取り込むを押す  ③ サイクル先頭から一周再生"];
    _message.frame = NSMakeRect(16, 22, 680, 58);
    _message.font = [NSFont systemFontOfSize:12];
    _message.textColor = [NSColor colorWithWhite:.86 alpha:1];
    [self addSubview:_message];
    __weak MerlaiPhrasePanel *weak = self;
    _timer = [NSTimer scheduledTimerWithTimeInterval:.12 repeats:YES
      block:^(NSTimer *t) { [weak poll]; }];
  }
  return self;
}
- (void)dealloc { [_timer invalidate]; }
- (void)poll {
  CaptureInfo info{}; UInt32 size = sizeof(info);
  if (AudioUnitGetProperty(_unit, CaptureProgress, 0, 0, &info, &size) != noErr)
    return;
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
    size = sizeof(Phrase);
    if (AudioUnitGetProperty(_unit, ReadPhrase, 0, 0, &_original, &size) == noErr) {
      _current = _original; _loaded = true; _progress.doubleValue = 1;
      _captureSummary.stringValue = [NSString stringWithFormat:
        @"%@ → %@  •  %u音を取り込み済み", BeatLabel(_original.start),
        BeatLabel(_original.end), _original.count];
      [_roll setOriginal:_original]; [_roll setProposal:_original visible:NO];
      _plan.enabled = _originalButton.enabled = YES;
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
- (void)arm:(id)sender {
  UInt32 value = 1;
  if (AudioUnitSetProperty(_unit, Arm, 0, 0, &value, sizeof(value)) == noErr) {
    _loaded = false; _undo.clear(); [_roll clear];
    _apply.enabled = _plan.enabled = _originalButton.enabled =
      _revisedButton.enabled = _undoButton.enabled = NO;
    _captureSummary.stringValue = @"待機中 — 再生位置をサイクル先頭へ移動して再生";
    _message.stringValue = @"取り込み待機中です。Logicをサイクル先頭から再生してください。";
  }
}
- (void)setMode:(BOOL)revised {
  UInt32 value = revised;
  AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &value, sizeof(value));
  _message.stringValue = revised
    ? @"修正案を選択中。次のサイクル先頭から切り替わります。"
    : @"原案を選択中。次のサイクル先頭から切り替わります。";
}
- (void)original:(id)sender { [self setMode:NO]; }
- (void)revised:(id)sender {
  if (_loaded && !_undo.empty()) [self setMode:YES];
}
- (void)plan:(id)sender {
  _apply.enabled = NO;
  if (!_loaded) { _message.stringValue = @"先に原案を取り込んでください。"; return; }
  _draft = _current;
  int n = merlai_edit(_current.notes.data(), _current.count,
    _current.end - _current.start, _instruction.stringValue.UTF8String,
    _draft.notes.data());
  if (n < 0) {
    _message.stringValue =
      @"指示を解釈できませんでした。「後半だけ半分に」「休符を増やして」などを試してください。";
    [_roll setProposal:_current visible:NO]; return;
  }
  _draft.count = n; [_roll setProposal:_draft visible:YES];
  _message.stringValue = [NSString stringWithFormat:
    @"プレビュー: 青 %u音 → オレンジ %d音。よければ適用してください。",
    _current.count, n];
  _apply.enabled = YES;
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
  if (![self submit:_draft]) return;
  _undo.push_back(_current); _current = _draft; _apply.enabled = NO;
  _revisedButton.enabled = _undoButton.enabled = YES;
  [_roll setProposal:_current visible:YES]; [self setMode:YES];
}
- (void)undoEdit:(id)sender {
  if (_undo.empty() || ![self submit:_undo.back()]) return;
  _current = _undo.back(); _undo.pop_back(); _apply.enabled = NO;
  _undoButton.enabled = _revisedButton.enabled = !_undo.empty();
  [_roll setProposal:_current visible:!_undo.empty()];
  [self setMode:!_undo.empty()];
}
@end

@interface MerlaiPhraseViewFactory : NSObject <AUCocoaUIBase>
@end
@implementation MerlaiPhraseViewFactory
- (unsigned)interfaceVersion { return 0; }
- (NSView *)uiViewForAudioUnit:(AudioUnit)unit withSize:(NSSize)size {
  return [[MerlaiPhrasePanel alloc] initWithUnit:unit];
}
@end
