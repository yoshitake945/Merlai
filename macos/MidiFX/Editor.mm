#include "Phrase.h"
#import <AudioUnit/AUCocoaUIView.h>
#import <Cocoa/Cocoa.h>
#include <vector>

@interface MerlaiPhrasePanel : NSView {
  AudioUnit _unit;
  Phrase _original, _current, _draft;
  std::vector<Phrase> _undo;
  NSTextField *_instruction, *_message;
  NSButton *_apply;
  NSTimer *_timer;
  bool _loaded;
}
- (instancetype)initWithUnit:(AudioUnit)unit;
@end

@implementation MerlaiPhrasePanel
- (NSButton *)button:(NSString *)title
              action:(SEL)action
                   x:(int)x
                   y:(int)y
               width:(int)w {
  NSButton *b = [NSButton buttonWithTitle:title target:self action:action];
  b.frame = NSMakeRect(x, y, w, 30);
  [self addSubview:b];
  return b;
}
- (instancetype)initWithUnit:(AudioUnit)unit {
  if ((self = [super initWithFrame:NSMakeRect(0, 0, 560, 210)])) {
    _unit = unit;
    [self button:@"フレーズを取り込む"
          action:@selector(arm:)
               x:12
               y:164
           width:165];
    [self button:@"原案" action:@selector(original:) x:181 y:164 width:75];
    [self button:@"修正案" action:@selector(revised:) x:260 y:164 width:80];
    [self button:@"一手戻す" action:@selector(undoEdit:) x:355 y:164 width:100];
    _instruction =
        [[NSTextField alloc] initWithFrame:NSMakeRect(15, 122, 525, 26)];
    _instruction.stringValue = @"後半だけ音数を半分に。最後の音は残して";
    [self addSubview:_instruction];
    [self button:@"変更内容を確認" action:@selector(plan:) x:12 y:80 width:150];
    _apply = [self button:@"適用して比較"
                   action:@selector(apply:)
                        x:170
                        y:80
                    width:140];
    _apply.enabled = NO;
    _message = [NSTextField
        wrappingLabelWithString:@"Logicでサイクルを指定して取り込みを押し、先頭"
                                @"から再生してください。"];
    _message.frame = NSMakeRect(16, 10, 525, 60);
    [self addSubview:_message];
    __weak MerlaiPhrasePanel *weak = self;
    _timer = [NSTimer scheduledTimerWithTimeInterval:0.20
                                             repeats:YES
                                               block:^(NSTimer *t) {
                                                 [weak poll];
                                               }];
  }
  return self;
}
- (void)dealloc {
  [_timer invalidate];
}
- (void)poll {
  if (_loaded)
    return;
  UInt32 state = 0, size = sizeof(state);
  if (AudioUnitGetProperty(_unit, Status, 0, 0, &state, &size) != 0)
    return;
  if (state == 3) {
    size = sizeof(Phrase);
    if (AudioUnitGetProperty(_unit, ReadPhrase, 0, 0, &_original, &size) ==
        noErr) {
      _current = _original;
      _loaded = true;
      _message.stringValue = [NSString
          stringWithFormat:
              @"原案を取り込みました（%u音）。指示を入力してください。",
              _original.count];
    }
  } else if (state == 2)
    _message.stringValue =
        @"取り込み中。サイクルが一周するまで再生してください。";
  else if (state == 4)
    _message.stringValue = @"取り込めませんでした。ノートのあるサイクルを指定し"
                           @"、もう一度取り込んでください。";
}
- (void)arm:(id)sender {
  UInt32 value = 1;
  if (AudioUnitSetProperty(_unit, Arm, 0, 0, &value, sizeof(value)) == noErr) {
    _loaded = false;
    _undo.clear();
    _apply.enabled = NO;
    _message.stringValue = @"サイクルの先頭を待っています。";
  }
}
- (void)setMode:(BOOL)revised {
  UInt32 value = revised;
  AudioUnitSetProperty(_unit, PlaybackMode, 0, 0, &value, sizeof(value));
  _message.stringValue = revised ? @"次のサイクルで修正案を再生します。"
                                 : @"次のサイクルで原案を再生します。";
}
- (void)original:(id)sender {
  [self setMode:NO];
}
- (void)revised:(id)sender {
  if (_loaded && !_undo.empty())
    [self setMode:YES];
}
- (void)plan:(id)sender {
  _apply.enabled = NO;
  if (!_loaded) {
    _message.stringValue = @"先に原案を取り込んでください。";
    return;
  }
  _draft = _current;
  int n = merlai_edit(_current.notes.data(), _current.count,
                      _current.end - _current.start,
                      _instruction.stringValue.UTF8String, _draft.notes.data());
  if (n < 0) {
    _message.stringValue = @"指示を確認してください。「休符を増やして」「もう少"
                           @"し減らして」などに対応します。";
    return;
  }
  _draft.count = n;
  _message.stringValue = [NSString
      stringWithFormat:@"「%@」 全体 %u音 → %d音。適用して比較できます。",
                       _instruction.stringValue, _current.count, n];
  _apply.enabled = YES;
}
- (BOOL)submit:(const Phrase &)p {
  if (AudioUnitSetProperty(_unit, Submit, 0, 0, &p, sizeof(p)) != noErr) {
    _message.stringValue =
        @"前の変更が反映されるまでサイクル再生を続けてください。";
    return NO;
  }
  return YES;
}
- (void)apply:(id)sender {
  if (![self submit:_draft])
    return;
  _undo.push_back(_current);
  _current = _draft;
  _apply.enabled = NO;
  [self setMode:YES];
}
- (void)undoEdit:(id)sender {
  if (_undo.empty())
    return;
  if (![self submit:_undo.back()])
    return;
  _current = _undo.back();
  _undo.pop_back();
  _apply.enabled = NO;
  [self setMode:!_undo.empty()];
}
@end

@interface MerlaiPhraseViewFactory : NSObject <AUCocoaUIBase>
@end
@implementation MerlaiPhraseViewFactory
- (unsigned)interfaceVersion {
  return 0;
}
- (NSView *)uiViewForAudioUnit:(AudioUnit)unit withSize:(NSSize)size {
  return [[MerlaiPhrasePanel alloc] initWithUnit:unit];
}
@end
