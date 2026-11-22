#include "../../macos/MidiFX/Link.h"
#include <cassert>
#include <cstring>
#include <cstdio>

int main() {
  const uint64_t source = merlai_link_register();
  const uint64_t destination = merlai_link_register();
  merlai_link_rename(source, "Melody");
  merlai_link_set_kind(source, 1);
  Phrase phrase{};
  phrase.start = 12;
  phrase.end = 20;
  phrase.notes[0] = {0, .5, 60, 90, 0};
  phrase.notes[1] = {1, 1.5, 64, 88, 0};
  phrase.count = 2;
  merlai_link_publish(source, phrase);

  LinkSourceInfo sources[2]{};
  assert(merlai_link_list(destination, sources, 2) == 1);
  assert(sources[0].id == source && sources[0].count == 2 && sources[0].kind == 1);
  assert(std::strcmp(sources[0].name, "Melody") == 0);
  Phrase copy{};
  uint64_t revision = 0;
  assert(merlai_link_read(source, copy, revision));
  assert(revision == 1 && copy.start == 12 && copy.end == 20 && copy.count == 2);

  merlai_link_unregister(source);
  assert(merlai_link_list(destination, sources, 2) == 0);
  merlai_link_unregister(destination);
  std::puts("Linked phrase publish, select, read and removal passed.");
}

