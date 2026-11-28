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

Run `scripts/build-midi-fx.sh` for the complete automated check. When a request for Logic-facing changes includes creating a PR, installation is part of completion: copy the signed component to `~/Library/Audio/Plug-Ins/Components`, verify its signature, and run `auval -v aumi MrFx Mrla` before handing off the PR. Do not quit or restart a running Logic process automatically; report that Logic must be restarted to load the installed binary. For other Logic-facing work, install when requested. Record the cycle range, IME/input scenario, progress, completion, piano-roll result, installation, and `auval` result.
