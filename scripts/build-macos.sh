#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
cargo build --locked --release
swift build --package-path macos --build-system native -c release
swift_bin=$(swift build --package-path macos --build-system native -c release --show-bin-path)
bundle=dist/Merlai.app/Contents
mkdir -p "$bundle/MacOS"
cp "$swift_bin/Merlai" "$swift_bin/Host" "$swift_bin/ModelBridge" target/release/merlai-compose "$bundle/MacOS/"
cp macos/Info.plist "$bundle/"
codesign --force --sign - "$bundle/MacOS/Host"
codesign --force --sign - "$bundle/MacOS/merlai-compose"
codesign --force --sign - "$bundle/MacOS/ModelBridge"
codesign --force --sign - dist/Merlai.app
codesign --verify --deep --strict dist/Merlai.app
