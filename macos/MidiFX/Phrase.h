#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
struct Note {
  double start, end;
  uint8_t pitch, velocity, channel;
};
constexpr size_t Capacity = 2048;
struct Phrase {
  std::array<Note, Capacity> notes{};
  uint32_t count = 0;
  double start = 0, end = 0;
};
extern "C" int32_t merlai_edit(const Note *, size_t, double, const char *,
                               Note *);
// Custom AU properties. The host marshals data between the Cocoa view and
// component.
enum : unsigned { Arm = 65000, ReadPhrase, Submit, PlaybackMode, Status };
