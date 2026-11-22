// Integration check for the installed component. Simulates a two-beat host
// loop.
#include "../../macos/MidiFX/Phrase.h"
#include <AudioToolbox/AudioToolbox.h>
#include <CoreMIDI/CoreMIDI.h>
#include <cassert>
#include <cstdio>
#include <vector>
struct Host {
  double beat = 0, rate = 44100, tempo = 0;
  bool playing = true;
  std::vector<int> keys;
  static OSStatus timing(void *ctx, double *beat, double *tempo) {
    auto &h = *static_cast<Host *>(ctx);
    if (beat)
      *beat = h.beat;
    if (tempo)
      *tempo = h.tempo;
    return noErr;
  }
  static OSStatus transport(void *ctx, Boolean *playing, Boolean *changed,
                            double *sample, Boolean *cycle, double *start,
                            double *end) {
    if (playing)
      *playing = static_cast<Host *>(ctx)->playing;
    if (changed)
      *changed = false;
    if (sample)
      *sample = 0;
    if (cycle)
      *cycle = true;
    if (start)
      *start = 0;
    if (end)
      *end = 2;
    return noErr;
  }
  static OSStatus output(void *ctx, const AudioTimeStamp *, UInt32,
                         const MIDIPacketList *list) {
    auto &h = *static_cast<Host *>(ctx);
    const auto *p = &list->packet[0];
    for (unsigned i = 0; i < list->numPackets; i++, p = MIDIPacketNext(p)) {
      if ((p->data[0] & 0xf0) == 0x90 && p->data[2])
        h.keys.push_back(p->data[1]);
    }
    return noErr;
  }
};
int main() {
  Host h;
  AudioComponentDescription desc = {'aumi', 'MrFx', 'Mrla', 0, 0};
  auto comp = AudioComponentFindNext(nullptr, &desc);
  assert(comp);
  AudioUnit au = nullptr;
  assert(AudioComponentInstanceNew(comp, &au) == 0);
  auto set = [&](UInt32 id, const auto &value) {
    assert(AudioUnitSetProperty(au, id, 0, 0, &value, sizeof(value)) == 0);
  };
  HostCallbackInfo callbacks{};
  callbacks.hostUserData = &h;
  callbacks.beatAndTempoProc = Host::timing;
  callbacks.transportStateProc = Host::transport;
  set(kAudioUnitProperty_HostCallbacks, callbacks);
  set(kAudioUnitProperty_MIDIOutputCallback,
      AUMIDIOutputCallbackStruct{Host::output, &h});
  assert(AudioUnitInitialize(au) == 0);
  AudioStreamBasicDescription fmt{};
  UInt32 size = sizeof(fmt);
  assert(AudioUnitGetProperty(au, kAudioUnitProperty_StreamFormat,
                              kAudioUnitScope_Output, 0, &fmt, &size) == 0);
  h.tempo = 60 * fmt.mSampleRate / 256;
  struct {
    UInt32 count;
    AudioBuffer buffers[2];
  } out{2, {{1, 1024, nullptr}, {1, 1024, nullptr}}};
  double sample = 0;
  auto block = [&](int beat, double hostOffset = 0.) {
    h.beat = beat + hostOffset;
    AudioTimeStamp t{};
    t.mSampleTime = sample;
    t.mFlags = kAudioTimeStampSampleTimeValid;
    sample += 256;
    for (int i = 0; i < 4; i++) {
      UInt32 k = 60 + beat * 4 + i;
      assert(!MusicDeviceMIDIEvent(au, 0x90, k, 80, i * 64));
      assert(!MusicDeviceMIDIEvent(au, 0x80, k, 0, i * 64 + 32));
    }
    for (auto &b : out.buffers) {
      b.mData = nullptr;
      b.mDataByteSize = 1024;
    }
    AudioUnitRenderActionFlags flags = 0;
    assert(!AudioUnitRender(au, &flags, &t, 0, 256,
                            reinterpret_cast<AudioBufferList *>(&out)));
  };
  set(Arm, 1u);
  CaptureInfo capture{};
  size = sizeof(capture);
  assert(!AudioUnitGetProperty(au, CaptureProgress, 0, 0, &capture, &size));
  assert(capture.state == Armed && capture.count == 0);
  block(0);
  size = sizeof(capture);
  assert(!AudioUnitGetProperty(au, CaptureProgress, 0, 0, &capture, &size));
  assert(capture.state == Capturing && capture.start == 0 &&
         capture.end == 2 && capture.count == 4);
  block(1, 3.0 / 256); // Host beat and nominal render end can differ by a few frames.
  block(0);
  size = sizeof(capture);
  assert(!AudioUnitGetProperty(au, CaptureProgress, 0, 0, &capture, &size));
  assert(capture.state == Ready && capture.count == 8);
  Phrase p{};
  size = sizeof(p);
  assert(!AudioUnitGetProperty(au, ReadPhrase, 0, 0, &p, &size));
  assert(p.count == 8);
  Phrase proposal = p;
  proposal.count = merlai_edit(p.notes.data(), p.count, 2,
                               "後半だけ音数を半分に。最後の音は残して",
                               proposal.notes.data());
  assert(proposal.count == 6);
  set(Submit, proposal);
  set(PlaybackMode, 1u);
  block(1);
  h.keys.clear();
  block(0);
  block(1);
  assert((h.keys == std::vector<int>{60, 61, 62, 63, 65, 67}));
  set(PlaybackMode, 0u);
  h.keys.clear();
  block(0);
  block(1);
  assert(h.keys.size() == 8);
  AudioUnitUninitialize(au);
  AudioComponentInstanceDispose(au);
  puts("Capture 8, edit 6, original 8: installed Audio Unit host round-trip "
       "passed.");
}
