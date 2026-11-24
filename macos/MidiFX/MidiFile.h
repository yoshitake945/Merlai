#pragma once
#include "Phrase.h"
#include <cstdint>
#include <vector>

// Encodes a Phrase as a tempo-independent Standard MIDI File (format 0).
// Note positions are relative to the beginning of the phrase so the host's
// drop position determines where the resulting region starts.
std::vector<uint8_t> merlai_midi_file(const Phrase &phrase);
