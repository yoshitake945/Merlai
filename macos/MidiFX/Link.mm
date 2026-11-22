#include "Link.h"
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <vector>

namespace {
struct Entry {
  LinkSourceInfo info;
  Phrase phrase;
};
std::mutex registryMutex;
std::vector<Entry> registry;
std::atomic<uint64_t> nextId{1};
} // namespace

uint64_t merlai_link_register() {
  const uint64_t id = nextId.fetch_add(1);
  Entry entry{};
  entry.info.id = id;
  std::snprintf(entry.info.name, sizeof(entry.info.name), "Merlai %llu",
                static_cast<unsigned long long>(id));
  std::lock_guard lock(registryMutex);
  registry.push_back(entry);
  return id;
}

void merlai_link_unregister(uint64_t id) {
  std::lock_guard lock(registryMutex);
  std::erase_if(registry, [id](const Entry &entry) { return entry.info.id == id; });
}

void merlai_link_rename(uint64_t id, const char *name) {
  if (!name || !*name)
    return;
  std::lock_guard lock(registryMutex);
  auto found = std::find_if(registry.begin(), registry.end(),
                            [id](const Entry &entry) { return entry.info.id == id; });
  if (found != registry.end()) {
    std::strncpy(found->info.name, name, sizeof(found->info.name) - 1);
    found->info.name[sizeof(found->info.name) - 1] = 0;
  }
}

void merlai_link_set_kind(uint64_t id, uint32_t kind) {
  std::lock_guard lock(registryMutex);
  auto found = std::find_if(registry.begin(), registry.end(),
                            [id](const Entry &entry) { return entry.info.id == id; });
  if (found != registry.end())
    found->info.kind = kind;
}

void merlai_link_publish(uint64_t id, const Phrase &phrase) {
  std::lock_guard lock(registryMutex);
  auto found = std::find_if(registry.begin(), registry.end(),
                            [id](const Entry &entry) { return entry.info.id == id; });
  if (found == registry.end())
    return;
  found->phrase = phrase;
  found->info.count = phrase.count;
  found->info.start = phrase.start;
  found->info.end = phrase.end;
  ++found->info.revision;
}

size_t merlai_link_list(uint64_t exclude, LinkSourceInfo *output,
                        size_t capacity) {
  std::lock_guard lock(registryMutex);
  size_t count = 0;
  for (const Entry &entry : registry) {
    if (entry.info.id == exclude || !entry.info.count)
      continue;
    if (count < capacity)
      output[count] = entry.info;
    ++count;
  }
  return count;
}

bool merlai_link_read(uint64_t id, Phrase &output, uint64_t &revision) {
  std::lock_guard lock(registryMutex);
  auto found = std::find_if(registry.begin(), registry.end(),
                            [id](const Entry &entry) { return entry.info.id == id; });
  if (found == registry.end() || !found->info.count)
    return false;
  output = found->phrase;
  revision = found->info.revision;
  return true;
}
