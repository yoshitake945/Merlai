#include "../../macos/MidiFX/Phrase.h"
#import <Cocoa/Cocoa.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#include <cassert>
#include <cstdio>

extern "C" NSView *merlai_ui_test_create(void);
extern "C" void merlai_ui_test_load_phrase(NSView *, const Phrase *);
extern "C" uint32_t merlai_ui_test_draft_count(NSView *);
extern "C" void merlai_ui_test_set_candidate(NSView *, const Phrase *);
extern "C" void merlai_ui_test_export_phrase(NSView *, Phrase *);
extern "C" NSURL *merlai_ui_test_drag_url(NSView *);
extern "C" id<NSPasteboardWriting> merlai_ui_test_drag_writer(NSView *);
extern "C" void merlai_ui_test_show_response(NSView *, NSDictionary *);

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

    auto *prompt = (NSTextView *)find(panel, @"merlai.instruction");
    auto *tabs = (NSSegmentedControl *)find(panel, @"merlai.tabs");
    NSView *generation = find(panel, @"merlai.generation");
    NSView *editor = find(panel, @"merlai.editor");
    NSView *roll = find(panel, @"merlai.editor-roll");
    auto *assistant = (NSTextView *)find(panel, @"merlai.assistant-message");
    NSView *drag = find(panel, @"merlai.midi-drag");
    assert(prompt && tabs && generation && editor && roll && assistant && drag);
    assert([prompt.accessibilityLabel isEqualToString:@"生成指示"]);
    assert([roll.accessibilityLabel isEqualToString:@"MIDIノート編集領域"]);
    NSArray<NSString *> *firstMouseIDs = @[@"merlai.instruction", @"merlai.source",
      @"merlai.purpose", @"merlai.provider", @"merlai.model", @"merlai.endpoint",
      @"merlai.plan", @"merlai.generate", @"merlai.tabs", @"merlai.editor-roll",
      @"merlai.editor-copy", @"merlai.editor-undo", @"merlai.editor-audition",
      @"merlai.editor-confirm"];
    NSEvent *probe = [NSEvent mouseEventWithType:NSEventTypeLeftMouseDown location:NSZeroPoint
      modifierFlags:0 timestamp:0 windowNumber:window.windowNumber context:nil eventNumber:0
      clickCount:1 pressure:1];
    for (NSString *identifier in firstMouseIDs) {
      NSView *control = find(panel, identifier);
      assert(control && [control acceptsFirstMouse:probe]);
    }
    assert([window makeFirstResponder:prompt]);
    id responder = window.firstResponder;
    assert([responder conformsToProtocol:@protocol(NSTextInputClient)]);
    [prompt selectAll:nil];
    [responder setMarkedText:@"すとりんぐすをついか" selectedRange:NSMakeRange(10, 0)
            replacementRange:NSMakeRange(NSNotFound, 0)];
    assert([responder hasMarkedText]);
    [responder insertText:@"ストリングスを追加" replacementRange:NSMakeRange(NSNotFound, 0)];
    assert(![responder hasMarkedText]);
    assert([prompt.string isEqualToString:@"ストリングスを追加"]);

    Phrase phrase{}; phrase.start = 12; phrase.end = 16; phrase.count = 2;
    phrase.notes[0] = {0, 1, 60, 90, 0};
    phrase.notes[1] = {2, 3, 64, 90, 0};
    merlai_ui_test_load_phrase(panel, &phrase);
    Phrase candidate = phrase; candidate.count = 1; candidate.notes[0].pitch = 72;
    merlai_ui_test_set_candidate(panel, &candidate);
    assert([[drag valueForKey:@"enabled"] boolValue]);
    assert(![[drag valueForKey:@"confirmed"] boolValue]);
    Phrase exported{}; merlai_ui_test_export_phrase(panel, &exported);
    assert(exported.count == 1 && exported.notes[0].pitch == 72);
    NSURL *dragURL = merlai_ui_test_drag_url(panel);
    assert(dragURL.isFileURL && [[NSFileManager defaultManager] fileExistsAtPath:dragURL.path]);
    id<NSPasteboardWriting> dragWriter = merlai_ui_test_drag_writer(panel);
    assert([dragWriter isKindOfClass:NSFilePromiseProvider.class]);
    assert([((NSFilePromiseProvider *)dragWriter).fileType isEqualToString:UTTypeData.identifier]);

    NSString *longMessage = @"主旋律を避けるため音域を上げ、長い音価のストリングスにしました。次の候補も選べます。";
    merlai_ui_test_show_response(panel, @{@"message": longMessage,
      @"suggestions": @[@"音数を減らす", @"一オクターブ下げる", @"終止だけ伸ばす"]});
    assert([assistant.string isEqualToString:longMessage]);
    for (NSUInteger i = 0; i < 3; ++i) {
      auto *suggestion = (NSButton *)find(panel,
        [NSString stringWithFormat:@"merlai.suggestion.%lu", (unsigned long)i]);
      assert(suggestion && !suggestion.hidden);
    }
    auto *firstSuggestion = (NSButton *)find(panel, @"merlai.suggestion.0");
    [firstSuggestion sendAction:firstSuggestion.action to:firstSuggestion.target];
    assert([prompt.string isEqualToString:@"音数を減らす"]);
    merlai_ui_test_show_response(panel, @{@"message": @"更新しました", @"suggestions": @[@"弱くする"]});
    assert(!firstSuggestion.hidden);
    assert(((NSButton *)find(panel, @"merlai.suggestion.1")).hidden);
    assert(((NSButton *)find(panel, @"merlai.suggestion.2")).hidden);
    assert([firstSuggestion acceptsFirstMouse:probe]);
    assert([drag acceptsFirstMouse:probe]);

    tabs.selectedSegment = 1;
    [tabs sendAction:tabs.action to:tabs.target];
    assert(generation.hidden && !editor.hidden);
    assert(merlai_ui_test_draft_count(panel) == candidate.count);
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
      [prompt selectAll:nil];
      responder = window.firstResponder;
      NSString *value = [NSString stringWithFormat:@"指示-%d-strings", cycle];
      [responder insertText:value replacementRange:NSMakeRange(NSNotFound, 0)];
      assert([prompt.string isEqualToString:value]);
      tabs.selectedSegment = 1;
      [tabs sendAction:tabs.action to:tabs.target];
      assert(generation.hidden && !editor.hidden && window.firstResponder == roll);
    }
    puts("AU Cocoa UI focus, tab visibility, accessibility, and hit testing passed.");
  }
}
