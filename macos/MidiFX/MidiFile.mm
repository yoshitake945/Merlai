#include "MidiFile.h"
#include <algorithm>
#include <cmath>

namespace {
constexpr uint16_t PPQ = 960;

void u16(std::vector<uint8_t> &out, uint16_t value) {
  out.push_back(value >> 8);
  out.push_back(value & 0xff);
}
void u32(std::vector<uint8_t> &out, uint32_t value) {
  out.push_back(value >> 24);
  out.push_back((value >> 16) & 0xff);
  out.push_back((value >> 8) & 0xff);
  out.push_back(value & 0xff);
}
void vlq(std::vector<uint8_t> &out, uint32_t value) {
  uint8_t bytes[5] = {uint8_t(value & 0x7f)};
  size_t count = 1;
  while ((value >>= 7) != 0)
    bytes[count++] = uint8_t(0x80 | (value & 0x7f));
  while (count) out.push_back(bytes[--count]);
}
struct Event {
  uint32_t tick;
  uint8_t status, pitch, velocity;
};
}

std::vector<uint8_t> merlai_midi_file(const Phrase &phrase) {
  std::vector<Event> events;
  events.reserve(std::min<uint32_t>(phrase.count, Capacity) * 2);
  const uint32_t count = std::min<uint32_t>(phrase.count, Capacity);
  for (uint32_t i = 0; i < count; ++i) {
    const Note &note = phrase.notes[i];
    if (!std::isfinite(note.start) || !std::isfinite(note.end) ||
        note.start < 0 || note.end < note.start || note.pitch > 127 ||
        note.velocity > 127 || note.channel > 15)
      continue;
    uint32_t start = uint32_t(std::llround(note.start * PPQ));
    uint32_t end = uint32_t(std::llround(note.end * PPQ));
    events.push_back({start, uint8_t(0x90 | note.channel), note.pitch,
                      note.velocity});
    events.push_back({end, uint8_t(0x80 | note.channel), note.pitch, 0});
  }
  std::sort(events.begin(), events.end(), [](const Event &a, const Event &b) {
    if (a.tick != b.tick) return a.tick < b.tick;
    // End a repeated note before starting its successor at the same tick.
    if ((a.status & 0xf0) != (b.status & 0xf0))
      return (a.status & 0xf0) == 0x80;
    if (a.pitch != b.pitch) return a.pitch < b.pitch;
    return a.status < b.status;
  });

  std::vector<uint8_t> track;
  const char name[] = "Merlai Candidate";
  vlq(track, 0); track.insert(track.end(), {0xff, 0x03, sizeof(name) - 1});
  track.insert(track.end(), name, name + sizeof(name) - 1);
  uint32_t previous = 0;
  for (const Event &event : events) {
    vlq(track, event.tick - previous);
    track.insert(track.end(), {event.status, event.pitch, event.velocity});
    previous = event.tick;
  }
  double duration = std::isfinite(phrase.end - phrase.start)
    ? std::max(0.0, phrase.end - phrase.start) : 0.0;
  uint32_t finalTick = std::max(previous, uint32_t(std::llround(duration * PPQ)));
  vlq(track, finalTick - previous); track.insert(track.end(), {0xff, 0x2f, 0x00});

  std::vector<uint8_t> file;
  file.insert(file.end(), {'M', 'T', 'h', 'd'}); u32(file, 6);
  u16(file, 0); u16(file, 1); u16(file, PPQ);
  file.insert(file.end(), {'M', 'T', 'r', 'k'}); u32(file, uint32_t(track.size()));
  file.insert(file.end(), track.begin(), track.end());
  return file;
}
