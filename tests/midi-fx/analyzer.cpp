#include "../../macos/MidiFX/Phrase.h"
#include <AudioToolbox/AudioToolbox.h>
#include <cassert>
#include <cstdio>
#include <cstring>

struct Host {
  double beat = 0, tempo = 0;
  static OSStatus timing(void *context, double *beat, double *tempo) {
    auto &host = *static_cast<Host *>(context);
    *beat = host.beat;
    *tempo = host.tempo;
    return noErr;
  }
  static OSStatus transport(void *, Boolean *playing, Boolean *changed,
                            double *sample, Boolean *cycling, double *left,
                            double *right) {
    *playing = true;
    if (changed) *changed = false;
    if (sample) *sample = 0;
    *cycling = true;
    *left = 0;
    *right = 2;
    return noErr;
  }
  static OSStatus input(void *, AudioUnitRenderActionFlags *,
                        const AudioTimeStamp *, UInt32, UInt32 frames,
                        AudioBufferList *data) {
    for (UInt32 channel = 0; channel < data->mNumberBuffers; ++channel) {
      auto *samples = static_cast<float *>(data->mBuffers[channel].mData);
      std::memset(samples, 0, frames * sizeof(float));
      samples[10] = channel == 0 ? 1.f : .5f;
      data->mBuffers[channel].mDataByteSize = frames * sizeof(float);
    }
    return noErr;
  }
};

int main() {
  AudioComponentDescription description = {'aufx', 'MrAn', 'Mrla', 0, 0};
  AudioComponent component = AudioComponentFindNext(nullptr, &description);
  assert(component);
  AudioUnit unit = nullptr;
  assert(AudioComponentInstanceNew(component, &unit) == noErr);
  Host host;
  HostCallbackInfo hostCallbacks{};
  hostCallbacks.hostUserData = &host;
  hostCallbacks.beatAndTempoProc = Host::timing;
  hostCallbacks.transportStateProc = Host::transport;
  assert(AudioUnitSetProperty(unit, kAudioUnitProperty_HostCallbacks,
                              kAudioUnitScope_Global, 0, &hostCallbacks,
                              sizeof(hostCallbacks)) == noErr);
  AURenderCallbackStruct input{Host::input, &host};
  assert(AudioUnitSetProperty(unit, kAudioUnitProperty_SetRenderCallback,
                              kAudioUnitScope_Input, 0, &input,
                              sizeof(input)) == noErr);
  UInt32 maximumFrames = 2048;
  assert(AudioUnitSetProperty(unit, kAudioUnitProperty_MaximumFramesPerSlice,
                              kAudioUnitScope_Global, 0, &maximumFrames,
                              sizeof(maximumFrames)) == noErr);
  assert(AudioUnitInitialize(unit) == noErr);
  AudioStreamBasicDescription format{};
  UInt32 size = sizeof(format);
  assert(AudioUnitGetProperty(unit, kAudioUnitProperty_StreamFormat,
                              kAudioUnitScope_Output, 0, &format, &size) == noErr);
  host.tempo = 60. * format.mSampleRate / maximumFrames;
  UInt32 arm = 1;
  assert(AudioUnitSetProperty(unit, Arm, 0, 0, &arm, sizeof(arm)) == noErr);
  float left[2048]{}, right[2048]{};
  struct {
    UInt32 count;
    AudioBuffer buffers[2];
  } output{2, {{1, sizeof(left), left}, {1, sizeof(right), right}}};
  for (int beat = 0; beat < 2; ++beat) {
    host.beat = beat;
    AudioTimeStamp time{};
    time.mFlags = kAudioTimeStampSampleTimeValid;
    time.mSampleTime = beat * maximumFrames;
    AudioUnitRenderActionFlags flags = 0;
    assert(AudioUnitRender(unit, &flags, &time, 0, maximumFrames,
                           reinterpret_cast<AudioBufferList *>(&output)) == noErr);
    assert(left[10] == 1.f && right[10] == .5f);
  }
  Phrase onsets{};
  size = sizeof(onsets);
  assert(AudioUnitGetProperty(unit, ReadPhrase, 0, 0, &onsets, &size) == noErr);
  assert(onsets.count == 2);
  assert(onsets.notes[0].pitch == 36 &&
         onsets.notes[1].start == 1. + 10. / maximumFrames);
  AudioUnitUninitialize(unit);
  AudioComponentInstanceDispose(unit);
  std::puts("Audio pass-through and two-onset cycle capture passed.");
}

