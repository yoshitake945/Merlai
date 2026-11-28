---
name: merlai-native-app
description: Develop and verify Merlai's Rust composer, Swift macOS app, Audio Unit host helper, or ModelBridge. Use for crates, macos/Sources, MIDI generation, standalone audition, model bridging, or app bundling; not for the Logic MIDI FX UI.
---

# Merlai Native App

Start from [docs/development.md](../../../docs/development.md), then read [docs/native-engine.md](../../../docs/native-engine.md) for Rust generation or [macos/README.md](../../../macos/README.md) for the Swift app and audio-host workflow.

Keep generated MIDI deterministic for the same input and seed. Do not move Audio Unit loading into the Rust composer or model/network work into an audio render thread. Preserve the JSON boundary between Swift, ModelBridge, and the composer unless an explicit interface change is requested and documented.

Run `cargo fmt --check`, `cargo test --locked`, and `scripts/build-macos.sh` in proportion to the touched subsystem. For sound-profile or audition changes, record the instrument, preset handling, rendered result, and whether saved profiles still reload.
