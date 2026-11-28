---
name: merlai-release
description: Prepare and verify Merlai CI, macOS artifacts, version tags, and GitHub draft releases. Use for release readiness, macos-v tags, workflow failures, artifact inspection, or publishing preparation; not for ordinary feature implementation.
---

# Merlai Release

Read [CONTRIBUTING.md](../../../CONTRIBUTING.md) and inspect `.github/workflows/native.yml` before release work. A release candidate must pass the Rust engine job and the macOS job, including both app and MIDI FX builds and signature checks.

Use the exact tested commit for a `macos-v*` tag. Inspect the downloaded ZIP, supported macOS/architecture, signatures, and recorded real-device results before recommending publication. Tag creation and release publication are external mutations: prepare evidence first and perform them only when explicitly requested. The workflow intentionally creates a draft release; do not publish it implicitly.
