#pragma once
#include "Phrase.h"
#include <cstddef>
#include <cstdint>

struct LinkSourceInfo {
  uint64_t id = 0, revision = 0;
  char name[64]{};
  uint32_t count = 0;
  double start = 0, end = 0;
};

uint64_t merlai_link_register();
void merlai_link_unregister(uint64_t id);
void merlai_link_rename(uint64_t id, const char *name);
void merlai_link_publish(uint64_t id, const Phrase &phrase);
size_t merlai_link_list(uint64_t exclude, LinkSourceInfo *output,
                        size_t capacity);
bool merlai_link_read(uint64_t id, Phrase &output, uint64_t &revision);

