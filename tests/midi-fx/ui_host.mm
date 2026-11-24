#include "../../macos/MidiFX/Phrase.h"
#import <Cocoa/Cocoa.h>
#include <cassert>
#include <cstdio>

extern "C" NSView *merlai_ui_test_create(void);
extern "C" void merlai_ui_test_load_phrase(NSView *, const Phrase *);
extern "C" uint32_t merlai_ui_test_draft_count(NSView *);

static NSView *find(NSView *root, NSString *identifier) {
  if ([root.accessibilityIdentifier isEqualToString:identifier]) return root;
  for (NSView *child in root.subviews)
    if (NSView *match = find(child, identifier)) return match;
  return nil;
}

int main() {
  @autoreleasepool {
    [NSApplication sharedApplication];
    NSView *panel = merlai_ui_test_create();
    assert(panel);
    NSWindow *window = [[NSWindow alloc]
      initWithContentRect:NSMakeRect(0, 0, 960, 720)
                styleMask:NSWindowStyleMaskTitled backing:NSBackingStoreBuffered defer:NO];
    window.contentView = panel;

    auto *prompt = (NSTextField *)find(panel, @"merlai.instruction");
    auto *tabs = (NSSegmentedControl *)find(panel, @"merlai.tabs");
    NSView *generation = find(panel, @"merlai.generation");
    NSView *editor = find(panel, @"merlai.editor");
    NSView *roll = find(panel, @"merlai.editor-roll");
    assert(prompt && tabs && generation && editor && roll);
    assert([prompt.accessibilityLabel isEqualToString:@"生成指示"]);
    assert([roll.accessibilityLabel isEqualToString:@"MIDIノート編集領域"]);
    assert([window makeFirstResponder:prompt]);
    [prompt selectText:nil];
    id responder = window.firstResponder;
    assert([responder conformsToProtocol:@protocol(NSTextInputClient)]);
    [responder insertText:@"ストリングスを追加" replacementRange:NSMakeRange(NSNotFound, 0)];
    assert([prompt.stringValue isEqualToString:@"ストリングスを追加"]);

    Phrase phrase{}; phrase.start = 12; phrase.end = 16; phrase.count = 2;
    phrase.notes[0] = {0, 1, 60, 90, 0};
    phrase.notes[1] = {2, 3, 64, 90, 0};
    merlai_ui_test_load_phrase(panel, &phrase);
    tabs.selectedSegment = 1;
    [tabs sendAction:tabs.action to:tabs.target];
    assert(generation.hidden && !editor.hidden);
    assert(merlai_ui_test_draft_count(panel) == phrase.count);
    assert(window.firstResponder == roll);

    NSArray<NSString *> *buttonIDs = @[@"merlai.editor-copy", @"merlai.editor-undo",
      @"merlai.editor-audition", @"merlai.editor-confirm"];
    for (NSString *identifier in buttonIDs) {
      NSView *button = find(panel, identifier);
      assert(button && !button.hidden);
      NSPoint center = [button convertPoint:NSMakePoint(NSMidX(button.bounds), NSMidY(button.bounds))
                                     toView:panel];
      NSView *hit = [panel hitTest:center];
      assert(hit == button || [hit isDescendantOf:button]);
    }

    for (int cycle = 0; cycle < 32; ++cycle) {
      tabs.selectedSegment = 0;
      [tabs sendAction:tabs.action to:tabs.target];
      assert(!generation.hidden && editor.hidden);
      assert([window makeFirstResponder:prompt]);
      [prompt selectText:nil];
      responder = window.firstResponder;
      NSString *value = [NSString stringWithFormat:@"指示-%d-strings", cycle];
      [responder insertText:value replacementRange:NSMakeRange(NSNotFound, 0)];
      assert([prompt.stringValue isEqualToString:value]);
      tabs.selectedSegment = 1;
      [tabs sendAction:tabs.action to:tabs.target];
      assert(generation.hidden && !editor.hidden && window.firstResponder == roll);
    }
    puts("AU Cocoa UI focus, tab visibility, accessibility, and hit testing passed.");
  }
}
