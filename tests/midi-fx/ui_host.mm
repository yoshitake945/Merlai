#include "../../macos/MidiFX/Phrase.h"
#import <Cocoa/Cocoa.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#include <cassert>
#include <cstdio>

extern "C" NSView *merlai_ui_test_create(void);
extern "C" void merlai_ui_test_load_phrase(NSView *, const Phrase *);
extern "C" uint32_t merlai_ui_test_draft_count(NSView *);
extern "C" BOOL merlai_ui_test_is_editing_text(NSView *);
extern "C" void merlai_ui_test_set_capture(NSView *, const CaptureInfo *, const Phrase *);
extern "C" void merlai_ui_test_poll(NSView *);
extern "C" BOOL merlai_ui_test_is_loaded(NSView *);
extern "C" NSUInteger merlai_ui_test_source_refreshes(NSView *);
extern "C" void merlai_ui_test_set_candidate(NSView *, const Phrase *);
extern "C" void merlai_ui_test_export_phrase(NSView *, Phrase *);
extern "C" NSURL *merlai_ui_test_drag_url(NSView *);
extern "C" id<NSPasteboardWriting> merlai_ui_test_drag_writer(NSView *);
extern "C" void merlai_ui_test_show_response(NSView *, NSDictionary *);
extern "C" void merlai_ui_test_append_conversation(NSView *, NSString *, NSString *);
extern "C" NSUInteger merlai_ui_test_conversation_count(NSView *);

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
    auto *placeholder = (NSTextField *)find(panel, @"merlai.instruction-placeholder");
    auto *sourceName = (NSTextField *)find(panel, @"merlai.source-name");
    auto *endpoint = (NSTextField *)find(panel, @"merlai.endpoint");
    auto *captureSummary = (NSTextField *)find(panel, @"merlai.capture-summary");
    auto *captureProgress = (NSProgressIndicator *)find(panel, @"merlai.capture-progress");
    auto *tabs = (NSSegmentedControl *)find(panel, @"merlai.tabs");
    NSView *generation = find(panel, @"merlai.generation");
    NSView *editor = find(panel, @"merlai.editor");
    NSView *roll = find(panel, @"merlai.editor-roll");
    auto *purpose = (NSPopUpButton *)find(panel, @"merlai.purpose");
    auto *keyScale = (NSPopUpButton *)find(panel, @"merlai.key-scale");
    auto *assistant = (NSTextView *)find(panel, @"merlai.assistant-message");
    NSView *drag = find(panel, @"merlai.midi-drag");
    assert(prompt && placeholder && sourceName && endpoint && captureSummary && captureProgress &&
           tabs && generation && editor && roll && purpose && keyScale && assistant && drag);
    assert([prompt.accessibilityLabel isEqualToString:@"生成指示"]);
    assert(placeholder.accessibilityElement == NO);
    assert(placeholder.hidden);
    assert([roll.accessibilityLabel isEqualToString:@"MIDI候補差分表示"]);
    assert(purpose.numberOfItems == 5);
    assert([purpose itemWithTitle:@"続きを生成"] != nil);
    assert(keyScale.numberOfItems == 25);
    assert([keyScale itemWithTitle:@"C Major"] != nil);
    assert([keyScale itemWithTitle:@"B Minor"] != nil);
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
    assert(merlai_ui_test_is_editing_text(panel));
    id responder = window.firstResponder;
    assert([responder conformsToProtocol:@protocol(NSTextInputClient)]);
    [prompt selectAll:nil];
    [responder setMarkedText:@"すとりんぐすをついか" selectedRange:NSMakeRange(10, 0)
            replacementRange:NSMakeRange(NSNotFound, 0)];
    assert([responder hasMarkedText]);
    [responder insertText:@"ストリングスを追加" replacementRange:NSMakeRange(NSNotFound, 0)];
    assert(![responder hasMarkedText]);
    assert([prompt.string isEqualToString:@"ストリングスを追加"]);
    assert(placeholder.hidden);

    prompt.string = @"";
    [prompt layoutSubtreeIfNeeded];
    assert(!placeholder.hidden);
    assert([placeholder.stringValue isEqualToString:@"作曲・編集の指示を入力"]);
    NSRect placeholderFrame = placeholder.frame;
    for (int redraw = 0; redraw < 16; ++redraw) {
      // Caret blinking and host refreshes invalidate only part of NSTextView.
      // A stable placeholder remains a separate subview with a fixed frame.
      [prompt setNeedsDisplayInRect:NSMakeRect(placeholderFrame.origin.x, 0, 2,
                                               NSHeight(prompt.bounds))];
      [prompt displayIfNeeded];
      assert(NSEqualRects(placeholder.frame, placeholderFrame));
      assert(!placeholder.hidden);
    }
    [window makeFirstResponder:endpoint];
    [placeholder mouseDown:probe];
    assert(window.firstResponder == prompt);
    [responder setMarkedText:@"へんかん" selectedRange:NSMakeRange(4, 0)
            replacementRange:NSMakeRange(NSNotFound, 0)];
    assert(placeholder.hidden);
    [responder unmarkText];
    prompt.string = @"";
    assert(!placeholder.hidden);

    // NSTextField uses a window-owned field editor rather than becoming the
    // first responder itself. Editing it is still detected without disturbing
    // the prompt placeholder.
    for (NSTextField *field in @[sourceName, endpoint]) {
      assert([window makeFirstResponder:field]);
      assert([window.firstResponder isKindOfClass:NSTextView.class]);
      assert(window.firstResponder != field);
      assert(merlai_ui_test_is_editing_text(panel));
      assert(!placeholder.hidden);
      assert(NSEqualRects(placeholder.frame, placeholderFrame));
    }

    Phrase phrase{}; phrase.start = 12; phrase.end = 16; phrase.count = 2;
    phrase.notes[0] = {0, 1, 60, 90, 0};
    phrase.notes[1] = {2, 3, 64, 90, 0};
    assert([window makeFirstResponder:prompt]);
    responder = window.firstResponder;
    [responder setMarkedText:@"後半をへんしゅう" selectedRange:NSMakeRange(8, 0)
            replacementRange:NSMakeRange(NSNotFound, 0)];
    NSUInteger refreshes = merlai_ui_test_source_refreshes(panel);
    CaptureInfo capture{Capturing, 7, 12, 16, 14};
    merlai_ui_test_set_capture(panel, &capture, &phrase);
    merlai_ui_test_poll(panel);
    assert([responder hasMarkedText]);
    assert(captureProgress.doubleValue == .5);
    assert([captureSummary.stringValue containsString:@"取り込み中 7音"]);
    assert(merlai_ui_test_source_refreshes(panel) == refreshes);
    capture.state = Ready; capture.position = 16;
    merlai_ui_test_set_capture(panel, &capture, &phrase);
    merlai_ui_test_poll(panel);
    assert([responder hasMarkedText]);
    assert(merlai_ui_test_is_loaded(panel));
    assert(captureProgress.doubleValue == 1);
    assert([captureSummary.stringValue containsString:@"2音を取り込み済み"]);
    [responder unmarkText];
    [window makeFirstResponder:nil];
    merlai_ui_test_poll(panel);
    assert(merlai_ui_test_source_refreshes(panel) == refreshes + 1);

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
    assert([dragWriter isKindOfClass:NSPasteboardItem.class]);
    NSPasteboardItem *dragItem = (NSPasteboardItem *)dragWriter;
    assert([dragItem.types containsObject:NSPasteboardTypeFileURL]);

    NSString *longMessage = @"主旋律を避けるため音域を上げ、長い音価のストリングスにしました。次の候補も選べます。";
    merlai_ui_test_append_conversation(panel, @"user", @"ストリングスを追加");
    merlai_ui_test_show_response(panel, @{@"message": longMessage,
      @"suggestions": @[@"音数を減らす", @"一オクターブ下げる", @"終止だけ伸ばす"]});
    assert([assistant.string containsString:@"あなた: ストリングスを追加"]);
    assert([assistant.string containsString:[@"Merlai: " stringByAppendingString:longMessage]]);
    for (NSUInteger i = 0; i < 3; ++i) {
      auto *suggestion = (NSButton *)find(panel,
        [NSString stringWithFormat:@"merlai.suggestion.%lu", (unsigned long)i]);
      assert(suggestion && !suggestion.hidden);
    }
    auto *firstSuggestion = (NSButton *)find(panel, @"merlai.suggestion.0");
    [firstSuggestion sendAction:firstSuggestion.action to:firstSuggestion.target];
    assert([prompt.string isEqualToString:@"音数を減らす"]);
    merlai_ui_test_append_conversation(panel, @"user", prompt.string);
    merlai_ui_test_show_response(panel, @{@"message": @"更新しました", @"suggestions": @[@"弱くする"]});
    assert(merlai_ui_test_conversation_count(panel) == 4);
    assert([assistant.string containsString:@"あなた: 音数を減らす"]);
    assert([assistant.string containsString:@"Merlai: 更新しました"]);
    assert(!firstSuggestion.hidden);
    assert(((NSButton *)find(panel, @"merlai.suggestion.1")).hidden);
    assert(((NSButton *)find(panel, @"merlai.suggestion.2")).hidden);
    assert([firstSuggestion acceptsFirstMouse:probe]);
    assert([drag acceptsFirstMouse:probe]);

    tabs.selectedSegment = 1;
    [tabs sendAction:tabs.action to:tabs.target];
    assert(generation.hidden && !editor.hidden);
    assert(merlai_ui_test_draft_count(panel) == candidate.count);
    assert(window.firstResponder != prompt);

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
      assert(generation.hidden && !editor.hidden && window.firstResponder != prompt);
    }
    puts("AU Cocoa UI focus, tab visibility, accessibility, and hit testing passed.");
  }
}
