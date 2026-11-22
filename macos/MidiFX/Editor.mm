#include "Phrase.h"
#include "Link.h"
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
  NSTextField *_sourceName;
  NSPopUpButton *_sourcePopup, *_purposePopup;
  NSButton *_plan, *_apply, *_originalButton, *_revisedButton, *_undoButton;
  NSProgressIndicator *_progress;
  MerlaiPianoRoll *_roll;
  NSTimer *_timer;
  uint64_t _instanceId, _sourcesSignature;
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
  if ((self = [super initWithFrame:NSMakeRect(0, 0, 720, 560)])) {
    self.wantsLayer = YES;
    self.layer.backgroundColor = [NSColor colorWithWhite:.13 alpha:1].CGColor;
    _unit = unit;
    UInt32 idSize = sizeof(_instanceId);
    AudioUnitGetProperty(_unit, InstanceID, 0, 0, &_instanceId, &idSize);
    [self label:@"Merlai フレーズ生成" frame:NSMakeRect(16, 528, 220, 24) size:17 bold:YES];
    [self label:@"1  入力を選ぶ" frame:NSMakeRect(240, 530, 100, 20) size:12 bold:YES];
    [self label:@"2  取り込む" frame:NSMakeRect(345, 530, 90, 20) size:12 bold:YES];
    [self label:@"3  候補を作る" frame:NSMakeRect(440, 530, 105, 20) size:12 bold:YES];
    [self label:@"4  比較・録音" frame:NSMakeRect(550, 530, 110, 20) size:12 bold:YES];
    [self button:@"2  フレーズを取り込む" action:@selector(arm:)
           frame:NSMakeRect(16, 483, 185, 32)];
    _captureSummary = [self label:@"未取り込み — Logicで先にサイクルを指定"
                            frame:NSMakeRect(216, 490, 480, 20) size:12 bold:NO];
    _progress = [[NSProgressIndicator alloc] initWithFrame:NSMakeRect(216, 479, 480, 8)];
    _progress.minValue = 0; _progress.maxValue = 1; _progress.indeterminate = NO;
    [self addSubview:_progress];
    [self label:@"共有名" frame:NSMakeRect(16, 447, 48, 20) size:11 bold:YES];
    _sourceName = [[NSTextField alloc] initWithFrame:NSMakeRect(64, 440, 112, 27)];
    _sourceName.stringValue = [NSString stringWithFormat:@"Merlai %llu",
      (unsigned long long)_instanceId];
    _sourceName.target = self; _sourceName.action = @selector(renameSource:);
    [self addSubview:_sourceName];
    _sourcePopup = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(184, 440, 232, 27)];
    [_sourcePopup addItemWithTitle:@"入力元: このトラック"];
    [self addSubview:_sourcePopup];
    [self button:@"入力を読み込む" action:@selector(loadSource:)
           frame:NSMakeRect(424, 440, 120, 27)];
    _purposePopup = [[NSPopUpButton alloc] initWithFrame:NSMakeRect(552, 440, 144, 27)];
    [_purposePopup addItemsWithTitles:@[@"生成: ベース", @"生成: コード", @"生成: 対旋律"]];
    [self addSubview:_purposePopup];
    _roll = [[MerlaiPianoRoll alloc] initWithFrame:NSMakeRect(16, 260, 680, 165)];
    _roll.wantsLayer = YES; _roll.layer.cornerRadius = 5;
    _roll.layer.masksToBounds = YES; [self addSubview:_roll];
    [self label:@"3  候補を生成、または文章で編集" frame:NSMakeRect(16, 226, 260, 22) size:13 bold:YES];
    _instruction = [[NSTextField alloc] initWithFrame:NSMakeRect(16, 188, 355, 30)];
    _instruction.stringValue = @"後半だけ音数を半分に。最後の音は残して";
    [self addSubview:_instruction];
    _plan = [self button:@"変更内容を確認" action:@selector(plan:)
                   frame:NSMakeRect(379, 188, 145, 30)];
    [self button:@"候補を生成" action:@selector(generate:)
           frame:NSMakeRect(532, 188, 164, 30)];
    _originalButton = [self button:@"原案を聴く" action:@selector(original:)
                             frame:NSMakeRect(16, 143, 112, 30)];
    _revisedButton = [self button:@"修正案を聴く" action:@selector(revised:)
                            frame:NSMakeRect(136, 143, 120, 30)];
    _apply = [self button:@"適用して修正案を聴く" action:@selector(apply:)
                    frame:NSMakeRect(264, 143, 190, 30)];
    _undoButton = [self button:@"一手戻す" action:@selector(undoEdit:)
                         frame:NSMakeRect(462, 143, 100, 30)];
    _apply.enabled = _plan.enabled = _originalButton.enabled =
        _revisedButton.enabled = _undoButton.enabled = NO;
    _message = [NSTextField wrappingLabelWithString:
      @"操作: ① Logicで黄色いサイクル範囲を指定  ② 取り込むを押す  ③ サイクル先頭から一周再生"];
    _message.frame = NSMakeRect(16, 60, 680, 62);
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
- (void)renameSource:(id)sender {
  merlai_link_rename(_instanceId, _sourceName.stringValue.UTF8String);
  _sourcesSignature = 0;
}
- (void)refreshSources {
  LinkSourceInfo entries[64]{};
  size_t count = std::min<size_t>(merlai_link_list(_instanceId, entries, 64), 64);
  uint64_t signature = count;
  for (size_t i = 0; i < count; ++i)
    signature ^= entries[i].id * 1099511628211ULL ^ entries[i].revision;
  if (signature == _sourcesSignature) return;
  uint64_t selected = _sourcePopup.selectedItem.representedObject
    ? [_sourcePopup.selectedItem.representedObject unsignedLongLongValue] : 0;
  [_sourcePopup removeAllItems];
  [_sourcePopup addItemWithTitle:@"入力元: このトラック"];
  _sourcePopup.lastItem.representedObject = @(0);
  for (size_t i = 0; i < count; ++i) {
    NSString *name = [NSString stringWithUTF8String:entries[i].name];
    NSString *kind = entries[i].kind == 1 ? @"音声" : @"MIDI";
    [_sourcePopup addItemWithTitle:[NSString stringWithFormat:@"入力元: %@ [%@] (%u)", name, kind, entries[i].count]];
    _sourcePopup.lastItem.representedObject = @(entries[i].id);
    if (entries[i].id == selected) [_sourcePopup selectItem:_sourcePopup.lastItem];
  }
  _sourcesSignature = signature;
}
- (void)poll {
  [self refreshSources];
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
      merlai_link_rename(_instanceId, _sourceName.stringValue.UTF8String);
      merlai_link_publish(_instanceId, _original);
      _sourcesSignature = 0;
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
- (void)loadSource:(id)sender {
  NSNumber *represented = _sourcePopup.selectedItem.representedObject;
  uint64_t source = represented ? represented.unsignedLongLongValue : 0;
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
  _original = _current = linked; _loaded = true; _undo.clear();
  [_roll setOriginal:_original]; [_roll setProposal:_original visible:NO];
  _progress.doubleValue = 1;
  _captureSummary.stringValue = [NSString stringWithFormat:@"%@ → %@  •  別トラックから%u音",
    BeatLabel(linked.start), BeatLabel(linked.end), linked.count];
  _plan.enabled = _originalButton.enabled = YES;
  _revisedButton.enabled = _undoButton.enabled = _apply.enabled = NO;
  _message.stringValue = @"別トラックの入力を読み込みました。生成目的を選び「候補を生成」を押してください。";
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
- (void)generate:(id)sender {
  _apply.enabled = NO;
  if (!_loaded) {
    _message.stringValue = @"先にこのトラックを取り込むか、別トラックの入力を読み込んでください。";
    return;
  }
  _draft = _current;
  uint32_t purpose = (uint32_t)_purposePopup.indexOfSelectedItem;
  int n = merlai_generate(_original.notes.data(), _original.count,
    _original.end - _original.start, purpose, _draft.notes.data());
  if (n < 0) {
    _message.stringValue = @"この入力から候補を生成できませんでした。ノートを含む範囲を選んでください。";
    return;
  }
  _draft.count = n;
  [_roll setProposal:_draft visible:YES];
  NSString *purposeName = @[@"ベース", @"コード", @"対旋律"][purpose];
  _message.stringValue = [NSString stringWithFormat:
    @"%@候補: 青 %u音 → オレンジ %d音。適用前のプレビューです。",
    purposeName, _original.count, n];
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
