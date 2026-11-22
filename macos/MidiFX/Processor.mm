#include "Phrase.h"
#include "Link.h"
#include <AudioUnitSDK/AUBase.h>
#include <AudioUnitSDK/AUPlugInDispatch.h>
#include <CoreMIDI/CoreMIDI.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstring>

class MerlaiFX : public ausdk::AUBase {
  using Base = ausdk::AUBase;
  struct Message {
    UInt32 offset;
    UInt8 status, a, b;
  };
  std::array<Message, 4096> queue{};
  size_t queued = 0;
  bool overflow = false, editing = false, wasPlaying = false;
  double previousEnd = -1;
  AUMIDIOutputCallbackStruct callback{};
  // The UI reads a finished capture only, and publishes one pending edit at a
  // time.
  Phrase captured, mailbox, active;
  std::atomic<int> state{Idle};
  std::atomic<uint32_t> captureCount{0};
  std::atomic<double> captureStart{0}, captureEnd{0}, capturePosition{0};
  const uint64_t instanceId;
  std::atomic<bool> pending{false}, wantEdit{false}, bypass{false};
  bool sounding[16][128]{};
  std::atomic<bool> resetRequested{false};
  struct Event {
    double beat;
    UInt8 status, a, b;
  };
  std::array<Event, Capacity * 2> events{};
  size_t eventCount = 0;
  // Ordered by the control thread before publication.
  std::array<Event, Capacity * 2> prepared{};
  size_t preparedCount = 0;
  void send(const AudioTimeStamp &time, UInt32 offset, UInt8 status, UInt8 a,
            UInt8 b) {
    if (!callback.midiOutputCallback)
      return;
    MIDIPacketList list{};
    auto *packet = MIDIPacketListInit(&list);
    const UInt8 data[] = {status, a, b};
    size_t length = ((status & 0xe0) == 0xc0) ? 2 : 3;
    MIDIPacketListAdd(&list, sizeof(list), packet, offset, length, data);
    callback.midiOutputCallback(callback.userData, &time, 0, &list);
    if ((status & 0xf0) == 0x90 || (status & 0xf0) == 0x80)
      sounding[status & 15][a] = ((status & 0xf0) == 0x90 && b != 0);
  }
  void silence(const AudioTimeStamp &time, UInt32 offset) {
    for (int ch = 0; ch < 16; ++ch)
      for (int k = 0; k < 128; ++k)
        if (sounding[ch][k])
          send(time, offset, 0x80 | ch, k, 0);
  }
  void capture(const Message &m, double beat) {
    double t = beat - captured.start;
    if ((m.status & 0xf0) == 0x90 && m.b) {
      if (captured.count == Capacity) {
        state = Failed;
        return;
      }
      captured.notes[captured.count++] = {t, -1, m.a, m.b,
                                          UInt8(m.status & 15)};
      captureCount.store(captured.count, std::memory_order_relaxed);
    } else if ((m.status & 0xf0) == 0x80 || (m.status & 0xf0) == 0x90) {
      for (unsigned i = captured.count; i > 0; --i) {
        auto &n = captured.notes[i - 1];
        if (n.end < 0 && n.channel == (m.status & 15) && n.pitch == m.a) {
          n.end = std::max(t, n.start + 0.00001);
          break;
        }
      }
    }
  }
  void finish() {
    for (unsigned i = 0; i < captured.count; ++i)
      if (captured.notes[i].end < 0)
        captured.notes[i].end = captured.end - captured.start;
    state = captured.count ? Ready : Failed;
  }
  void boundary(const AudioTimeStamp &time, UInt32 offset, double left,
                double right) {
    // A host can announce the same loop start in adjacent render calls.
    // Complete at the right edge so a repeated start cannot publish an empty capture.
    if (state == Armed) {
      captured.count = 0;
      captured.start = left;
      captured.end = right;
      captureStart.store(left, std::memory_order_relaxed);
      captureEnd.store(right, std::memory_order_relaxed);
      capturePosition.store(left, std::memory_order_relaxed);
      captureCount.store(0, std::memory_order_relaxed);
      state = Capturing;
    }
    if (pending.load()) {
      active = mailbox;
      eventCount = preparedCount;
      std::copy_n(prepared.begin(), eventCount, events.begin());
      pending = false;
    }
    bool next = wantEdit && !bypass && active.count && active.start == left &&
                active.end == right;
    if (editing || next)
      silence(time, offset);
    editing = next;
  }

public:
  explicit MerlaiFX(AudioComponentInstance instance)
      : Base(instance, 0, 1), instanceId(merlai_link_register()) {}
  ~MerlaiFX() override { merlai_link_unregister(instanceId); }
  bool CanScheduleParameters() const noexcept AUSDK_RTSAFE override {
    return false;
  }
  bool StreamFormatWritable(AudioUnitScope, AudioUnitElement) override {
    return true;
  }
  OSStatus Reset(AudioUnitScope scope, AudioUnitElement el) override {
    resetRequested = true;
    return Base::Reset(scope, el);
  }
  OSStatus MIDIEvent(UInt32 status, UInt32 a, UInt32 b,
                     UInt32 offset) AUSDK_RTSAFE override {
    if (queued == queue.size()) {
      overflow = true;
      return noErr;
    }
    if (status >= 0x80 && status < 0xf0)
      queue[queued++] = {offset, UInt8(status), UInt8(a & 127), UInt8(b & 127)};
    return noErr;
  }
  OSStatus Render(AudioUnitRenderActionFlags &flags, const AudioTimeStamp &time,
                  UInt32 frames) AUSDK_RTSAFE override {
    auto &buffers = Output(0).GetBufferList();
    for (unsigned i = 0; i < buffers.mNumberBuffers; ++i) {
      auto &b = buffers.mBuffers[i];
      if (b.mData)
        memset(b.mData, 0, b.mDataByteSize);
    }
    flags |= kAudioUnitRenderAction_OutputIsSilence;
    Boolean playing = false, cycling = false;
    double beat = 0, tempo = 0, left = 0, right = 0;
    bool clock = CallHostBeatAndTempo(&beat, &tempo) == noErr && tempo > 0 &&
                 CallHostTransportState(&playing, nullptr, nullptr, &cycling,
                                        &left, &right) == noErr;
    double step = tempo / (60. * Output(0).GetStreamFormat().mSampleRate);
    bool loop =
        clock && playing && cycling && right - left > step * 2 && step > 0;
    if (loop && state == Capturing)
      capturePosition.store(std::clamp(beat, left, right),
                            std::memory_order_relaxed);
    if (resetRequested.exchange(false) || overflow ||
        (wasPlaying && (!playing || !loop || bypass ||
                        std::abs(previousEnd - beat) > std::max(2u, frames) * step))) {
      if (loop && !overflow && state == Capturing &&
          std::abs(previousEnd - right) <= frames * step &&
          std::abs(beat - left) <= frames * step)
        finish();
      silence(time, 0);
      editing = false;
      if (state == Capturing &&
          (!loop || overflow || std::abs(beat - left) > 2 * step))
        state = Failed;
    }
    if (!loop || bypass)
      editing = false;
    size_t input = 0;
    auto segment = [&](UInt32 begin, UInt32 end, double pos) {
      if (loop && pos >= left - step && pos <= left + step)
        boundary(time, begin, left, right);
      auto first =
          std::lower_bound(events.begin(), events.begin() + eventCount,
                           pos - active.start - 0.5 * step,
                           [](const Event &e, double b) { return e.beat < b; });
      for (UInt32 f = begin; f < end; ++f) {
        const double now = pos + (f - begin) * step;
        while (input < queued && queue[input].offset <= f) {
          const auto &m = queue[input++];
          bool isNote = (m.status & 0xe0) == 0x80;
          if (loop && state == Capturing && now >= left && now < right)
            capture(m, now);
          if (!(editing && isNote && now >= left && now < right))
            send(time, f, m.status, m.a, m.b);
        }
        if (editing)
          while (first != events.begin() + eventCount &&
                 active.start + first->beat <= now + 0.5 * step) {
            send(time, f, first->status, first->a, first->b);
            ++first;
          }
      }
    };
    UInt32 split = frames;
    if (loop && beat < right && beat + frames * step > right)
      split = std::clamp<long>(std::lround((right - beat) / step), 0, frames);
    if (loop && beat < left - step && beat + frames * step > left) {
      UInt32 start =
          std::clamp<long>(std::lround((left - beat) / step), 0, split);
      segment(0, start, beat);
      segment(start, split, left);
    } else
      segment(0, split, beat);
    if (loop && state == Capturing && beat < right &&
        beat + frames * step >= right - 0.5 * step)
      finish();
    if (split < frames)
      segment(split, frames, left);
    previousEnd = (split < frames ? left + (frames - split) * step
                                  : beat + frames * step);
    wasPlaying = playing;
    queued = 0;
    overflow = false;
    return noErr;
  }
  OSStatus GetPropertyInfo(AudioUnitPropertyID id, AudioUnitScope scope,
                           AudioUnitElement el, UInt32 &size,
                           bool &writable) override {
    if (scope != kAudioUnitScope_Global || el != 0)
      return Base::GetPropertyInfo(id, scope, el, size, writable);
    writable = false;
    switch (id) {
    case kAudioUnitProperty_CocoaUI:
      size = sizeof(AudioUnitCocoaViewInfo);
      return noErr;
    case kAudioUnitProperty_MIDIOutputCallbackInfo:
      size = sizeof(CFArrayRef);
      return noErr;
    case kAudioUnitProperty_MIDIOutputCallback:
      size = sizeof(callback);
      writable = true;
      return noErr;
    case ReadPhrase:
      size = sizeof(Phrase);
      return noErr;
    case Status:
      size = sizeof(UInt32);
      return noErr;
    case CaptureProgress:
      size = sizeof(CaptureInfo);
      return noErr;
    case InstanceID:
      size = sizeof(uint64_t);
      return noErr;
    case Submit:
      size = sizeof(Phrase);
      writable = true;
      return noErr;
    case Arm:
    case PlaybackMode:
    case kAudioUnitProperty_BypassEffect:
      size = sizeof(UInt32);
      writable = true;
      return noErr;
    default:
      return Base::GetPropertyInfo(id, scope, el, size, writable);
    }
  }
  OSStatus GetProperty(AudioUnitPropertyID id, AudioUnitScope scope,
                       AudioUnitElement el, void *out) override {
    if (scope != kAudioUnitScope_Global || el != 0)
      return Base::GetProperty(id, scope, el, out);
    switch (id) {
    case kAudioUnitProperty_CocoaUI: {
      auto *bundle = CFBundleGetBundleWithIdentifier(
          CFSTR("io.github.yoshitake945.Merlai.MidiFX"));
      if (!bundle)
        return kAudioUnitErr_InvalidPropertyValue;
      auto *info = (AudioUnitCocoaViewInfo *)out;
      info->mCocoaAUViewBundleLocation = CFBundleCopyBundleURL(bundle);
      info->mCocoaAUViewClass[0] =
          (CFStringRef)CFRetain(CFSTR("MerlaiPhraseViewFactory"));
      return noErr;
    }
    case kAudioUnitProperty_MIDIOutputCallbackInfo: {
      const void *name = CFSTR("Merlai");
      *(CFArrayRef *)out =
          CFArrayCreate(nullptr, &name, 1, &kCFTypeArrayCallBacks);
      return noErr;
    }
    case kAudioUnitProperty_MIDIOutputCallback:
      memcpy(out, &callback, sizeof(callback));
      return noErr;
    case Status:
      *(UInt32 *)out = state.load();
      return noErr;
    case CaptureProgress: {
      auto *info = static_cast<CaptureInfo *>(out);
      info->state = state.load();
      info->count = captureCount.load(std::memory_order_relaxed);
      info->start = captureStart.load(std::memory_order_relaxed);
      info->end = captureEnd.load(std::memory_order_relaxed);
      info->position = capturePosition.load(std::memory_order_relaxed);
      return noErr;
    }
    case InstanceID:
      *(uint64_t *)out = instanceId;
      return noErr;
    case ReadPhrase:
      if (state != Ready)
        return kAudioUnitErr_CannotDoInCurrentContext;
      memcpy(out, &captured, sizeof(Phrase));
      return noErr;
    case PlaybackMode:
      *(UInt32 *)out = wantEdit;
      return noErr;
    case kAudioUnitProperty_BypassEffect:
      *(UInt32 *)out = bypass;
      return noErr;
    default:
      return Base::GetProperty(id, scope, el, out);
    }
  }
  OSStatus SetProperty(AudioUnitPropertyID id, AudioUnitScope scope,
                       AudioUnitElement el, const void *data,
                       UInt32 size) override {
    if (scope != kAudioUnitScope_Global || el != 0)
      return Base::SetProperty(id, scope, el, data, size);
    if (id == kAudioUnitProperty_MIDIOutputCallback &&
        size == sizeof(callback)) {
      memcpy(&callback, data, size);
      return noErr;
    }
    if (id == Submit && size == sizeof(Phrase)) {
      if (pending)
        return kAudioUnitErr_CannotDoInCurrentContext;
      auto &p = *(const Phrase *)data;
      if (p.count > Capacity || !std::isfinite(p.start) ||
          !std::isfinite(p.end) || p.end <= p.start)
        return paramErr;
      for (unsigned i = 0; i < p.count; ++i) {
        const auto &n = p.notes[i];
        if (!std::isfinite(n.start) || !std::isfinite(n.end) || n.start < 0 ||
            n.end < n.start || n.end > p.end - p.start + 0.001 ||
            n.pitch > 127 || n.channel > 15 || n.velocity > 127)
          return paramErr;
      }
      mailbox = p;
      preparedCount = 0;
      for (unsigned i = 0; i < p.count; ++i) {
        const Note &n = p.notes[i];
        prepared[preparedCount++] = {n.start, UInt8(0x90 | n.channel), n.pitch,
                                     n.velocity};
        prepared[preparedCount++] = {n.end, UInt8(0x80 | n.channel), n.pitch,
                                     0};
      }
      std::sort(prepared.begin(), prepared.begin() + preparedCount,
                [](const Event &a, const Event &b) {
                  return a.beat == b.beat ? a.status < b.status
                                          : a.beat < b.beat;
                });
      pending = true;
      return noErr;
    }
    if (size == sizeof(UInt32)) {
      bool enabled = *(const UInt32 *)data != 0;
      if (id == Arm) {
        wantEdit = false;
        captureCount.store(0, std::memory_order_relaxed);
        captureStart.store(0, std::memory_order_relaxed);
        captureEnd.store(0, std::memory_order_relaxed);
        capturePosition.store(0, std::memory_order_relaxed);
        state = Armed;
        return noErr;
      }
      if (id == PlaybackMode) {
        wantEdit = enabled;
        return noErr;
      }
      if (id == kAudioUnitProperty_BypassEffect) {
        bypass = enabled;
        return noErr;
      }
    }
    return Base::SetProperty(id, scope, el, data, size);
  }
};
AUSDK_COMPONENT_ENTRY(ausdk::AUMIDIEffectFactory, MerlaiFX)
