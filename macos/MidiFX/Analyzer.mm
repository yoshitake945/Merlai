#include "Link.h"
#include "Phrase.h"
#include <AudioUnitSDK/AUEffectBase.h>
#include <AudioUnitSDK/AUPlugInDispatch.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstring>

class MerlaiAnalyzer : public ausdk::AUEffectBase {
  Phrase captured{};
  AudioAnalyzerState detector{};
  std::atomic<int> state{Idle};
  std::atomic<uint32_t> captureCount{0};
  std::atomic<double> captureStart{0}, captureEnd{0}, capturePosition{0};
  const uint64_t instanceId;
  bool blockLoop = false;
  double blockBeat = 0, blockStep = 0, loopLeft = 0, loopRight = 0;
  double previousBeat = -1;

  void begin(double left, double right) AUSDK_RTSAFE {
    captured = {};
    captured.start = left;
    captured.end = right;
    merlai_analyzer_reset(&detector);
    captureStart.store(left, std::memory_order_relaxed);
    captureEnd.store(right, std::memory_order_relaxed);
    capturePosition.store(left, std::memory_order_relaxed);
    captureCount.store(0, std::memory_order_relaxed);
    state.store(Capturing);
  }
  void finish() AUSDK_RTSAFE {
    state.store(captured.count ? Ready : Failed);
  }

public:
  explicit MerlaiAnalyzer(AudioComponentInstance instance)
      : AUEffectBase(instance), instanceId(merlai_link_register()) {
    merlai_link_set_kind(instanceId, 1);
    merlai_analyzer_reset(&detector);
  }
  ~MerlaiAnalyzer() override { merlai_link_unregister(instanceId); }

  OSStatus Render(AudioUnitRenderActionFlags &flags, const AudioTimeStamp &time,
                  UInt32 frames) AUSDK_RTSAFE override {
    Boolean playing = false, cycling = false;
    double beat = 0, tempo = 0, left = 0, right = 0;
    bool clock = CallHostBeatAndTempo(&beat, &tempo) == noErr && tempo > 0 &&
                 CallHostTransportState(&playing, nullptr, nullptr, &cycling,
                                        &left, &right) == noErr;
    const double rate = GetSampleRate();
    blockStep = rate > 0 ? tempo / (60. * rate) : 0;
    blockLoop = clock && playing && cycling && blockStep > 0 &&
                right > left + blockStep * 2;
    blockBeat = beat;
    loopLeft = left;
    loopRight = right;
    if (state.load() == Capturing && blockLoop && previousBeat >= 0 &&
        beat + blockStep < previousBeat)
      finish();
    if (state.load() == Armed && blockLoop &&
        beat >= left - blockStep && beat <= left + frames * blockStep)
      begin(left, right);
    if (state.load() == Capturing) {
      if (!blockLoop)
        state.store(Failed);
      else
        capturePosition.store(std::clamp(beat, left, right),
                              std::memory_order_relaxed);
    }
    OSStatus result = AUEffectBase::Render(flags, time, frames);
    previousBeat = beat;
    return result;
  }

  OSStatus ProcessBufferLists(AudioUnitRenderActionFlags &flags,
                              const AudioBufferList &input,
                              AudioBufferList &output,
                              UInt32 frames) AUSDK_RTSAFE override {
    const UInt32 buffers = std::min(input.mNumberBuffers, output.mNumberBuffers);
    for (UInt32 i = 0; i < buffers; ++i) {
      const AudioBuffer &in = input.mBuffers[i];
      AudioBuffer &out = output.mBuffers[i];
      if (in.mData && out.mData && in.mData != out.mData)
        std::memcpy(out.mData, in.mData,
                    std::min(in.mDataByteSize, out.mDataByteSize));
    }
    if (state.load() != Capturing || !blockLoop || !input.mNumberBuffers ||
        !input.mBuffers[0].mData)
      return noErr;
    const auto &format = Output(0).GetStreamFormat();
    if (format.mFormatID != kAudioFormatLinearPCM ||
        !(format.mFormatFlags & kAudioFormatFlagIsFloat) ||
        format.mBitsPerChannel != 32)
      return noErr;
    Onset onsets[64]{};
    size_t count = merlai_detect_onsets(
        &detector, static_cast<const float *>(input.mBuffers[0].mData), frames,
        format.mSampleRate, onsets, 64);
    for (size_t i = 0; i < count && captured.count < Capacity; ++i) {
      double absolute = blockBeat + onsets[i].frame * blockStep;
      if (absolute < loopLeft || absolute >= loopRight)
        continue;
      double relative = absolute - loopLeft;
      uint8_t velocity = static_cast<uint8_t>(
          std::clamp(35.f + onsets[i].strength * 90.f, 1.f, 127.f));
      captured.notes[captured.count++] = {
          relative, std::min(relative + .12, loopRight - loopLeft), 36,
          velocity, 0};
      captureCount.store(captured.count, std::memory_order_relaxed);
    }
    if (blockBeat < loopRight &&
        blockBeat + frames * blockStep >= loopRight - .5 * blockStep)
      finish();
    return noErr;
  }

  OSStatus GetPropertyInfo(AudioUnitPropertyID id, AudioUnitScope scope,
                           AudioUnitElement element, UInt32 &size,
                           bool &writable) override {
    if (scope != kAudioUnitScope_Global || element != 0)
      return AUEffectBase::GetPropertyInfo(id, scope, element, size, writable);
    writable = false;
    switch (id) {
    case kAudioUnitProperty_CocoaUI:
      size = sizeof(AudioUnitCocoaViewInfo);
      return noErr;
    case ReadPhrase:
      size = sizeof(Phrase);
      return noErr;
    case CaptureProgress:
      size = sizeof(CaptureInfo);
      return noErr;
    case Status:
      size = sizeof(UInt32);
      return noErr;
    case InstanceID:
      size = sizeof(uint64_t);
      return noErr;
    case Arm:
      size = sizeof(UInt32);
      writable = true;
      return noErr;
    default:
      return AUEffectBase::GetPropertyInfo(id, scope, element, size, writable);
    }
  }

  OSStatus GetProperty(AudioUnitPropertyID id, AudioUnitScope scope,
                       AudioUnitElement element, void *out) override {
    if (scope != kAudioUnitScope_Global || element != 0)
      return AUEffectBase::GetProperty(id, scope, element, out);
    switch (id) {
    case kAudioUnitProperty_CocoaUI: {
      auto *bundle = CFBundleGetBundleWithIdentifier(
          CFSTR("io.github.yoshitake945.Merlai.MidiFX"));
      if (!bundle)
        return kAudioUnitErr_InvalidPropertyValue;
      auto *info = static_cast<AudioUnitCocoaViewInfo *>(out);
      info->mCocoaAUViewBundleLocation = CFBundleCopyBundleURL(bundle);
      info->mCocoaAUViewClass[0] =
          (CFStringRef)CFRetain(CFSTR("MerlaiAnalyzerViewFactory"));
      return noErr;
    }
    case Status:
      *static_cast<UInt32 *>(out) = state.load();
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
    case ReadPhrase:
      if (state.load() != Ready)
        return kAudioUnitErr_CannotDoInCurrentContext;
      std::memcpy(out, &captured, sizeof(captured));
      return noErr;
    case InstanceID:
      *static_cast<uint64_t *>(out) = instanceId;
      return noErr;
    default:
      return AUEffectBase::GetProperty(id, scope, element, out);
    }
  }

  OSStatus SetProperty(AudioUnitPropertyID id, AudioUnitScope scope,
                       AudioUnitElement element, const void *data,
                       UInt32 size) override {
    if (scope == kAudioUnitScope_Global && element == 0 && id == Arm &&
        size == sizeof(UInt32)) {
      state.store(Armed);
      captureCount.store(0, std::memory_order_relaxed);
      return noErr;
    }
    return AUEffectBase::SetProperty(id, scope, element, data, size);
  }
};

AUSDK_COMPONENT_ENTRY(ausdk::AUBaseFactory, MerlaiAnalyzer)
