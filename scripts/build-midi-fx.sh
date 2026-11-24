#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
revision=bd98b31feff57a15989fcfab4cd86dc63382b1ac
sdk=${AUDIOUNIT_SDK:-target/AudioUnitSDK}
if [[ ! -d "$sdk" ]]; then
  git clone https://github.com/apple/AudioUnitSDK.git "$sdk"
  git -C "$sdk" checkout --detach "$revision"
fi
test "$(git -C "$sdk" rev-parse HEAD)" = "$revision"
cargo build --release --locked -p merlai-phrase-edit
swift build --package-path macos --build-system native -c release --product ModelBridge
swift_bin=$(swift build --package-path macos --build-system native -c release --show-bin-path)
out=dist/MerlaiFX.component/Contents
mkdir -p "$out/MacOS"
cp macos/MidiFX/Info.plist "$out/"
cp "$swift_bin/ModelBridge" "$out/MacOS/"
codesign --force --sign - "$out/MacOS/ModelBridge"
clang++ -std=c++23 -O2 -mmacosx-version-min=14.0 -fobjc-arc -bundle -I"$sdk/include" \
  "$sdk"/src/AudioUnitSDK/*.cpp macos/MidiFX/*.mm target/release/libmerlai_phrase_edit.a \
  -framework Cocoa -framework CoreMIDI -framework AudioUnit -framework AudioToolbox -framework CoreAudio -framework Accelerate -framework CoreFoundation \
  -o "$out/MacOS/MerlaiFX"
codesign --force --sign - dist/MerlaiFX.component
codesign --verify --strict dist/MerlaiFX.component
