import AVFoundation
import AppKit
import AudioUnit
import CSQLite
import CoreAudioKit
import CryptoKit

struct Failure: LocalizedError {
  let message: String
  init(_ s: String) { message = s }
  var errorDescription: String? { message }
}
struct Instrument: Codable {
  let id: String
  let name: String
}
struct Profile: Codable {
  let attack_ms: Double
  let release_ms: Double
  var tag: String = ""
}
struct Note: Codable {
  let at, len: Int
  let pitch, velocity: UInt8
}
struct Candidate: Decodable { let notes: [Note] }
struct Song: Decodable {
  let ppq, tempo, continuation_at: Int
  let melody: [Note]
  let candidates: [Candidate]
}
let rate = 44100.0
let storage = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
  .appendingPathComponent("Merlai")
func id(_ component: AVAudioUnitComponent) -> String {
  let d = component.audioComponentDescription
  return "\(d.componentManufacturer)-\(d.componentType)-\(d.componentSubType)"
}
func components() -> [AVAudioUnitComponent] {
  AVAudioUnitComponentManager.shared().components(
    matching: AudioComponentDescription(
      componentType: kAudioUnitType_MusicDevice, componentSubType: 0, componentManufacturer: 0,
      componentFlags: 0, componentFlagsMask: 0))
}
let protocolOutput = FileHandle(fileDescriptor: dup(STDOUT_FILENO), closeOnDealloc: true)
func emit<T: Encodable>(_ value: T) throws { protocolOutput.write(try JSONEncoder().encode(value)) }
func instrument(_ comp: AVAudioUnitComponent) throws -> AVAudioUnitMIDIInstrument {
  var result: Result<AVAudioUnit, Error>?
  AVAudioUnit.instantiate(with: comp.audioComponentDescription, options: []) { unit, error in
    result = unit.map { .success($0) } ?? .failure(error ?? Failure("Audio Unit load failed"))
  }
  while result == nil { RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.01)) }
  guard let unit = try result!.get() as? AVAudioUnitMIDIInstrument else {
    throw Failure("AU does not accept instrument MIDI")
  }
  return unit
}
final class Renderer {
  let engine = AVAudioEngine()
  let unit: AVAudioUnitMIDIInstrument
  let format = AVAudioFormat(standardFormatWithSampleRate: rate, channels: 2)!
  init(_ instrument: AVAudioUnitMIDIInstrument) throws {
    unit = instrument
    engine.attach(unit)
    engine.connect(unit, to: engine.mainMixerNode, format: format)
    try engine.enableManualRenderingMode(.offline, format: format, maximumFrameCount: 1024)
    try engine.start()
  }
  func frames(_ count: Int, consume: (AVAudioPCMBuffer) throws -> Void) throws {
    let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 1024)!
    var left = count
    while left > 0 {
      let n = AVAudioFrameCount(min(left, 1024))
      guard try engine.renderOffline(n, to: buffer) == .success, buffer.frameLength > 0 else {
        throw Failure("Instrument does not support offline rendering")
      }
      try consume(buffer)
      left -= Int(buffer.frameLength)
    }
  }
  func measure() throws -> Profile {
    var levels = [Double]()
    func sample(_ blocks: Int) throws {
      for _ in 0..<blocks {
        try frames(441) { buffer in
          var peak: Float = 0
          for channel in 0..<2 {
            for i in 0..<Int(buffer.frameLength) {
              peak = max(peak, abs(buffer.floatChannelData![channel][i]))
            }
          }
          levels.append(Double(peak))
        }
      }
    }
    unit.startNote(60, withVelocity: 90, onChannel: 0)
    try sample(100)
    unit.stopNote(60, onChannel: 0)
    try sample(200)
    let peak = levels.prefix(100).max() ?? 0
    guard peak > 0.0001 else { throw Failure("No audible response to middle C") }
    return Profile(
      attack_ms: Double(levels.firstIndex { $0 >= peak * 0.8 } ?? 0) * 10,
      release_ms: Double(levels.dropFirst(100).lastIndex { $0 > peak * 0.03 }.map { $0 - 99 } ?? 0)
        * 10)
  }
  func render(_ song: Song, index: Int, to url: URL) throws {
    guard song.candidates.indices.contains(index) else { throw Failure("Invalid candidate") }
    let scale = Double(song.tempo) * rate / 1_000_000 / Double(song.ppq)
    var events = [(Int, Bool, UInt8, UInt8)]()
    func add(_ notes: [Note], offset: Int) {
      for n in notes {
        events.append((Int(Double(offset + n.at) * scale), true, n.pitch, n.velocity))
        events.append((Int(Double(offset + n.at + n.len) * scale), false, n.pitch, 0))
      }
    }
    add(song.melody, offset: 0)
    add(song.candidates[index].notes, offset: song.continuation_at)
    events.sort { $0.0 == $1.0 ? (!$0.1 && $1.1) : $0.0 < $1.0 }
    guard (events.last?.0 ?? 0) < Int(rate * 600) else {
      throw Failure("Preview exceeds 10 minutes")
    }
    let file = try AVAudioFile(forWriting: url, settings: format.settings)
    var now = 0
    for (frame, on, key, vel) in events {
      try frames(frame - now) { try file.write(from: $0) }
      now = frame
      if on {
        unit.startNote(key, withVelocity: vel, onChannel: 0)
      } else {
        unit.stopNote(key, onChannel: 0)
      }
    }
    try frames(Int(rate * 2)) { try file.write(from: $0) }
  }
}
final class Editor: NSObject, NSWindowDelegate {
  var accepted = false
  let tagField = NSTextField(string: "")
  @objc func accept() {
    accepted = true
    NSApp.stop(nil)
  }
  func windowWillClose(_ notification: Notification) { NSApp.stop(nil) }
  func edit(_ unit: AVAudioUnitMIDIInstrument) throws {
    let app = NSApplication.shared
    app.setActivationPolicy(.regular)
    let window = NSWindow(
      contentRect: NSRect(x: 0, y: 0, width: 850, height: 640),
      styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
    window.isReleasedWhenClosed = false
    window.title = "Merlai — 音色を選択"
    window.delegate = self
    let stack = NSStackView()
    stack.orientation = .vertical
    let button = NSButton(title: "この音色を使う", target: self, action: #selector(accept))
    stack.addArrangedSubview(button)
    tagField.placeholderString = "用途タグ（任意、例：パッド）"
    stack.addArrangedSubview(tagField)
    var finished = false
    var controller: NSViewController?
    unit.auAudioUnit.requestViewController { vc in
      controller = vc
      finished = true
    }
    while !finished { RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.01)) }
    if let view = controller?.view {
      stack.addArrangedSubview(view)
    } else {
      stack.addArrangedSubview(NSTextField(labelWithString: "この音源は専用画面を提供していません。現在の音色を使用します。"))
    }
    window.contentView = stack
    window.center()
    window.makeKeyAndOrderFront(nil)
    app.activate(ignoringOtherApps: true)
    withExtendedLifetime(controller) { app.run() }
    guard accepted else { throw Failure("音色選択をキャンセルしました") }
  }
}
func cachedProfile(key: String, tag: String, renderer: Renderer) throws -> Profile {
  var db: OpaquePointer?
  guard sqlite3_open(storage.appendingPathComponent("catalog.sqlite").path, &db) == SQLITE_OK else {
    throw Failure("Cannot open timbre catalog")
  }
  defer { sqlite3_close(db) }
  // key is a hex SHA256 digest.
  guard
    sqlite3_exec(
      db, "CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, attack REAL, release REAL)",
      nil, nil, nil) == SQLITE_OK
  else { throw Failure("Cannot initialize catalog") }
  guard
    sqlite3_exec(
      db, "CREATE TABLE IF NOT EXISTS tags (id TEXT PRIMARY KEY, value TEXT)", nil, nil, nil)
      == SQLITE_OK
  else { throw Failure("Cannot initialize tags") }
  var tagStatement: OpaquePointer?
  guard
    sqlite3_prepare_v2(db, "INSERT OR REPLACE INTO tags VALUES (?,?)", -1, &tagStatement, nil)
      == SQLITE_OK
  else { throw Failure("Cannot prepare tag") }
  defer { sqlite3_finalize(tagStatement) }
  if !tag.isEmpty {
    let result = key.withCString { k in
      tag.withCString { t in
        sqlite3_bind_text(tagStatement, 1, k, -1, nil)
        sqlite3_bind_text(tagStatement, 2, t, -1, nil)
        return sqlite3_step(tagStatement)
      }
    }
    guard result == SQLITE_DONE else { throw Failure("Cannot save tag") }
  }
  var stmt: OpaquePointer?
  guard
    sqlite3_prepare_v2(
      db, "SELECT attack, release, value FROM profiles LEFT JOIN tags USING(id) WHERE id='\(key)'",
      -1, &stmt, nil) == SQLITE_OK
  else { throw Failure("Cannot read catalog") }
  defer { sqlite3_finalize(stmt) }
  if sqlite3_step(stmt) == SQLITE_ROW {
    return Profile(
      attack_ms: sqlite3_column_double(stmt, 0), release_ms: sqlite3_column_double(stmt, 1),
      tag: sqlite3_column_text(stmt, 2).map { String(cString: $0) } ?? "")
  }
  var p = try renderer.measure()
  p.tag = tag
  guard
    sqlite3_exec(
      db, "INSERT OR REPLACE INTO profiles VALUES ('\(key)',\(p.attack_ms),\(p.release_ms))", nil,
      nil, nil) == SQLITE_OK
  else { throw Failure("Cannot store timbre profile") }
  return p
}
func run() throws {
  let args = Array(CommandLine.arguments.dropFirst())
  let available = components()
  if args == ["list"] {
    try emit(available.map { Instrument(id: id($0), name: $0.name) })
    return
  }
  guard args.count >= 2, let comp = available.first(where: { id($0) == args[1] }) else {
    throw Failure("Unknown instrument")
  }
  try FileManager.default.createDirectory(at: storage, withIntermediateDirectories: true)
  let unit = try instrument(comp)
  let stateURL = storage.appendingPathComponent(args[1] + ".plist")
  if let data = try? Data(contentsOf: stateURL),
    let state = try PropertyListSerialization.propertyList(from: data, format: nil)
      as? [String: Any]
  {
    unit.auAudioUnit.fullState = state
  }
  if args[0] == "configure" {
    let renderer = try Renderer(unit)
    let editor = Editor()
    try editor.edit(unit)
    guard let state = unit.auAudioUnit.fullState else {
      throw Failure("Instrument cannot save its state")
    }
    let data = try PropertyListSerialization.data(
      fromPropertyList: state, format: .binary, options: 0)
    var fingerprint = Data("\(args[1])-\(comp.version)-v1".utf8)
    fingerprint.append(data)
    let key = SHA256.hash(data: fingerprint).map { String(format: "%02x", $0) }.joined()
    let p = try cachedProfile(key: key, tag: editor.tagField.stringValue, renderer: renderer)
    try data.write(to: stateURL, options: .atomic)
    try emit(p)
  } else if args[0] == "render", args.count == 5, let index = Int(args[3]) {
    let song = try JSONDecoder().decode(
      Song.self, from: Data(contentsOf: URL(fileURLWithPath: args[2])))
    try Renderer(unit).render(song, index: index, to: URL(fileURLWithPath: args[4]))
  } else {
    throw Failure("Unknown host command")
  }
}
_ = protocolOutput
dup2(STDERR_FILENO, STDOUT_FILENO)
do { try run() } catch {
  FileHandle.standardError.write(Data((error.localizedDescription + "\n").utf8))
  exit(1)
}
