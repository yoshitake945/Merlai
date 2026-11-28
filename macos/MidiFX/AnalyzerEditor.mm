#include "Link.h"
#include "Phrase.h"
#import <AudioUnit/AUCocoaUIView.h>
#import <Cocoa/Cocoa.h>

static BOOL MerlaiAnalyzerIsEditingTextInView(NSView *root) {
  NSResponder *responder = root.window.firstResponder;
  if (![responder isKindOfClass:NSTextView.class]) return NO;
  NSTextView *textView = (NSTextView *)responder;
  if (textView == root || [textView isDescendantOf:root]) return YES;
  id delegate = textView.delegate;
  return [delegate isKindOfClass:NSView.class] &&
    (delegate == root || [(NSView *)delegate isDescendantOf:root]);
}

@interface MerlaiAnalyzerPanel : NSView {
  AudioUnit _unit;
  uint64_t _instanceId;
  NSTextField *_name, *_status, *_summary;
  NSProgressIndicator *_progress;
  NSTimer *_timer;
  BOOL _published;
}
- (instancetype)initWithUnit:(AudioUnit)unit;
@end

@implementation MerlaiAnalyzerPanel
- (instancetype)initWithUnit:(AudioUnit)unit {
  if ((self = [super initWithFrame:NSMakeRect(0, 0, 520, 220)])) {
    self.wantsLayer = YES;
    self.layer.backgroundColor = [NSColor colorWithWhite:.13 alpha:1].CGColor;
    _unit = unit;
    UInt32 size = sizeof(_instanceId);
    AudioUnitGetProperty(_unit, InstanceID, 0, 0, &_instanceId, &size);
    NSTextField *title = [NSTextField labelWithString:@"Merlai Audio Analyzer"];
    title.frame = NSMakeRect(16, 184, 250, 24);
    title.font = [NSFont systemFontOfSize:17 weight:NSFontWeightSemibold];
    title.textColor = [NSColor colorWithWhite:.9 alpha:1];
    [self addSubview:title];
    NSTextField *nameLabel = [NSTextField labelWithString:@"共有名"];
    nameLabel.frame = NSMakeRect(16, 148, 50, 22);
    nameLabel.textColor = [NSColor colorWithWhite:.8 alpha:1];
    [self addSubview:nameLabel];
    _name = [[NSTextField alloc] initWithFrame:NSMakeRect(68, 145, 180, 27)];
    _name.stringValue = [NSString stringWithFormat:@"Drums %llu",
      (unsigned long long)_instanceId];
    _name.target = self; _name.action = @selector(rename:);
    [self addSubview:_name];
    NSButton *arm = [NSButton buttonWithTitle:@"ドラムを解析" target:self
                                       action:@selector(arm:)];
    arm.frame = NSMakeRect(270, 145, 130, 28);
    [self addSubview:arm];
    _summary = [NSTextField labelWithString:@"未解析 — Logicでサイクルを指定"];
    _summary.frame = NSMakeRect(16, 112, 480, 22);
    _summary.textColor = [NSColor colorWithWhite:.82 alpha:1];
    [self addSubview:_summary];
    _progress = [[NSProgressIndicator alloc] initWithFrame:NSMakeRect(16, 96, 480, 8)];
    _progress.minValue = 0; _progress.maxValue = 1; _progress.indeterminate = NO;
    [self addSubview:_progress];
    _status = [NSTextField wrappingLabelWithString:
      @"サイクル先頭から一周再生すると、オンセット位置と強度を入力元として公開します。原音は変更しません。"];
    _status.frame = NSMakeRect(16, 28, 480, 52);
    _status.textColor = [NSColor colorWithWhite:.82 alpha:1];
    [self addSubview:_status];
    merlai_link_set_kind(_instanceId, 1);
    merlai_link_rename(_instanceId, _name.stringValue.UTF8String);
    __weak MerlaiAnalyzerPanel *weak = self;
    _timer = [NSTimer scheduledTimerWithTimeInterval:.12 repeats:YES
      block:^(NSTimer *timer) { [weak poll]; }];
  }
  return self;
}
- (void)dealloc { [_timer invalidate]; }
- (void)rename:(id)sender {
  merlai_link_rename(_instanceId, _name.stringValue.UTF8String);
}
- (void)arm:(id)sender {
  UInt32 enabled = 1;
  if (AudioUnitSetProperty(_unit, Arm, 0, 0, &enabled, sizeof(enabled)) == noErr) {
    _published = NO;
    _progress.doubleValue = 0;
    _summary.stringValue = @"待機中 — サイクル先頭から再生";
  }
}
- (void)poll {
  // Avoid Audio Unit calls while AppKit's shared field editor is handling
  // typing or IME composition for the name field.
  if (MerlaiAnalyzerIsEditingTextInView(self)) return;
  CaptureInfo info{}; UInt32 size = sizeof(info);
  if (AudioUnitGetProperty(_unit, CaptureProgress, 0, 0, &info, &size) != noErr)
    return;
  if (info.state == Capturing && info.end > info.start) {
    _progress.doubleValue = (info.position - info.start) / (info.end - info.start);
    _summary.stringValue = [NSString stringWithFormat:@"解析中 • %uオンセット", info.count];
    _status.stringValue = @"原音を通過させながら解析中です。サイクル右端まで再生してください。";
  } else if (info.state == Ready && !_published) {
    Phrase phrase{}; size = sizeof(phrase);
    if (AudioUnitGetProperty(_unit, ReadPhrase, 0, 0, &phrase, &size) == noErr) {
      merlai_link_set_kind(_instanceId, 1);
      merlai_link_rename(_instanceId, _name.stringValue.UTF8String);
      merlai_link_publish(_instanceId, phrase);
      _published = YES; _progress.doubleValue = 1;
      _summary.stringValue = [NSString stringWithFormat:@"解析完了 • %uオンセット", phrase.count];
      _status.stringValue = @"Generator側の入力元一覧から、この共有名を選択できます。";
    }
  } else if (info.state == Failed) {
    _progress.doubleValue = 0;
    _summary.stringValue = @"解析失敗 — 音のあるサイクルを確認";
  }
}
@end

@interface MerlaiAnalyzerViewFactory : NSObject <AUCocoaUIBase>
@end
@implementation MerlaiAnalyzerViewFactory
- (unsigned)interfaceVersion { return 0; }
- (NSView *)uiViewForAudioUnit:(AudioUnit)unit withSize:(NSSize)size {
  return [[MerlaiAnalyzerPanel alloc] initWithUnit:unit];
}
@end
