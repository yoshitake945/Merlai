#include "../../macos/MidiFX/MidiFile.h"
#include <cassert>
#include <cstdint>
#include <vector>

static uint32_t be32(const std::vector<uint8_t> &data, size_t at) {
  return uint32_t(data[at]) << 24 | uint32_t(data[at + 1]) << 16 |
         uint32_t(data[at + 2]) << 8 | data[at + 3];
}

int main() {
  Phrase phrase{};
  phrase.start = 8; phrase.end = 10; phrase.count = 2;
  phrase.notes[0] = {0.5, 1.0, 60, 90, 0};
  phrase.notes[1] = {1.0, 1.5, 60, 100, 2};
  auto file = merlai_midi_file(phrase);
  assert(std::vector<uint8_t>(file.begin(), file.begin() + 4) ==
         std::vector<uint8_t>({'M', 'T', 'h', 'd'}));
  assert(be32(file, 4) == 6 && file[8] == 0 && file[9] == 0);
  assert(file[12] == 0x03 && file[13] == 0xc0); // 960 PPQ.
  assert(std::vector<uint8_t>(file.begin() + 14, file.begin() + 18) ==
         std::vector<uint8_t>({'M', 'T', 'r', 'k'}));

  // Track name, 480 ticks of leading rest, note-on, then at tick 960 the
  // first note-off must precede the next note-on.
  std::vector<uint8_t> expected = {
    0x00, 0xff, 0x03, 0x10, 'M','e','r','l','a','i',' ','C','a','n','d','i','d','a','t','e',
    0x83, 0x60, 0x90, 60, 90,
    0x83, 0x60, 0x80, 60, 0,
    0x00, 0x92, 60, 100,
    0x83, 0x60, 0x82, 60, 0,
    0x83, 0x60, 0xff, 0x2f, 0x00,
  };
  assert(be32(file, 18) == expected.size());
  assert(std::vector<uint8_t>(file.begin() + 22, file.end()) == expected);
}
