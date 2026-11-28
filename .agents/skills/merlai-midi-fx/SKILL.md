---
name: merlai-midi-fx
description: Develop, diagnose, build, install, and verify Merlai's Logic Pro AUv2 MIDI FX or Audio Analyzer. Use for files under macos/MidiFX, MIDI FX host/UI tests, Logic integration, component installation, or auval; not for the standalone Mac app.
---

# Merlai MIDI FX

Read [docs/midi-fx-development.md](../../../docs/midi-fx-development.md) before changing the AUv2 implementation. Read the relevant ADRs linked there when changing state boundaries, cross-track sharing, model transport, or analysis behavior.

Preserve these invariants:

- Never block MIDI or audio capture because a Cocoa text field or IME owns focus.
- Keep render-thread work fixed-size and free of locks, allocation, process launch, and file I/O.
- Treat building, installing the component, restarting Logic, and verifying the live UI as distinct steps. A running Logic process retains the previously loaded binary.
- Use redistributable test MIDI in the repository; keep production projects and commercial presets local.

Run `scripts/build-midi-fx.sh` for the complete automated check. For Logic-facing changes, install only when requested, run `auval -v aumi MrFx Mrla`, restart Logic safely, and record the cycle range, IME/input scenario, progress, completion, and piano-roll result.
