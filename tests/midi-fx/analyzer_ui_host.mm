#include "../../macos/MidiFX/Phrase.h"
#import <Cocoa/Cocoa.h>
#include <cassert>
#include <cstdio>

extern "C" NSView *merlai_analyzer_ui_test_create(void);
extern "C" void merlai_analyzer_ui_test_set_capture(NSView *, const CaptureInfo *,
                                                       const Phrase *);
extern "C" void merlai_analyzer_ui_test_poll(NSView *);
extern "C" BOOL merlai_analyzer_ui_test_is_editing_text(NSView *);
extern "C" BOOL merlai_analyzer_ui_test_is_published(NSView *);

static NSView *find(NSView *root, NSString *identifier) {
  if ([root.accessibilityIdentifier isEqualToString:identifier]) return root;
  for (NSView *child in root.subviews)
    if (NSView *match = find(child, identifier)) return match;
  return nil;
}

int main() {
  @autoreleasepool {
    [NSApplication sharedApplication];
    NSView *panel = merlai_analyzer_ui_test_create();
    NSWindow *window = [[NSWindow alloc]
      initWithContentRect:NSMakeRect(0, 0, 520, 220)
                styleMask:NSWindowStyleMaskTitled backing:NSBackingStoreBuffered defer:NO];
    window.contentView = panel;
    auto *name = (NSTextField *)find(panel, @"merlai.analyzer-name");
    auto *summary = (NSTextField *)find(panel, @"merlai.analyzer-summary");
    auto *progress = (NSProgressIndicator *)find(panel, @"merlai.analyzer-progress");
    assert(name && summary && progress);
    assert([window makeFirstResponder:name]);
    assert(merlai_analyzer_ui_test_is_editing_text(panel));
    id responder = window.firstResponder;
    [responder setMarkedText:@"ドラムへんしゅう" selectedRange:NSMakeRange(8, 0)
            replacementRange:NSMakeRange(NSNotFound, 0)];

    Phrase phrase{}; phrase.start = 0; phrase.end = 4; phrase.count = 3;
    CaptureInfo capture{Capturing, 3, 0, 4, 2};
    merlai_analyzer_ui_test_set_capture(panel, &capture, &phrase);
    merlai_analyzer_ui_test_poll(panel);
    assert([responder hasMarkedText]);
    assert(progress.doubleValue == .5);
    assert([summary.stringValue containsString:@"解析中 • 3オンセット"]);

    capture.state = Ready; capture.position = 4;
    merlai_analyzer_ui_test_set_capture(panel, &capture, &phrase);
    merlai_analyzer_ui_test_poll(panel);
    assert([responder hasMarkedText]);
    assert(merlai_analyzer_ui_test_is_published(panel));
    assert(progress.doubleValue == 1);
    assert([summary.stringValue containsString:@"解析完了 • 3オンセット"]);
    puts("Analyzer capture continues while its shared name is being edited.");
  }
}
