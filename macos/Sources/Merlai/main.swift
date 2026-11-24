import AVFoundation
import SwiftUI
import UniformTypeIdentifiers

struct Instrument: Codable, Identifiable { let id, name: String }
struct Profile: Codable {
  let attack_ms, release_ms: Double
  let tag: String
}
struct Request: Encodable {
  let version = 1
  let melody: String
  let drums: String?
  let output: String
  let bars, seed: Int
  let kicks: [Int]
  let tonic: Int?
  let attack_ms, release_ms: Double
}
struct Candidate: Decodable, Identifiable {
  let file: String
  var id: String { file }
}
struct Take {
  let directory: URL
  let candidates: [Candidate]
  let voice: String
  let drumVoice: String
}
struct Response: Decodable { let candidates: [Candidate] }
func helper(_ name: String, _ args: [String], input: Data? = nil) async throws -> Data {
  try await Task.detached {
    let process = Process()
    let folder = Bundle.main.executableURL!.deletingLastPathComponent()
    process.executableURL = folder.appendingPathComponent(name)
    process.arguments = args
    let output = Pipe()
    let stdin = Pipe()
    let diagnostic = FileManager.default.temporaryDirectory.appendingPathComponent(
      UUID().uuidString)
    try Data().write(to: diagnostic)
    defer { try? FileManager.default.removeItem(at: diagnostic) }
    let errors = try FileHandle(forWritingTo: diagnostic)
    defer { try? errors.close() }
    process.standardOutput = output
    process.standardError = errors
    process.standardInput = stdin
    try process.run()
    if let input { try stdin.fileHandleForWriting.write(contentsOf: input) }
    try stdin.fileHandleForWriting.close()
    let data = output.fileHandleForReading.readDataToEndOfFile()
    process.waitUntilExit()
    guard process.terminationStatus == 0 else {
      let message = (try? String(contentsOf: diagnostic, encoding: .utf8)) ?? ""
      throw NSError(
        domain: "Merlai", code: 1,
        userInfo: [NSLocalizedDescriptionKey: message.isEmpty ? "\(name) stopped" : message])
    }
    return data
  }.value
}
func midiProvider(_ path: String) -> NSItemProvider {
  let url = URL(fileURLWithPath: path)
  let provider = NSItemProvider()
  provider.registerObject(url as NSURL, visibility: .all)
  provider.registerFileRepresentation(
    forTypeIdentifier: UTType.midi.identifier, fileOptions: [], visibility: .all
  ) { completion in
    completion(url, false, nil)
    return nil
  }
  return provider
}
@MainActor final class ComposerModel: ObservableObject {
  @Published var melody: URL?
  @Published var drums: URL?
  @Published var instruments = [Instrument]()
  @Published var instrument = UserDefaults.standard.string(forKey: "instrument") ?? ""
  @Published var drumInstrument = UserDefaults.standard.string(forKey: "drumInstrument") ?? ""
  @Published var kickText = "36"
  @Published var tonic = -1
  @Published var bars = 2
  @Published var profile: Profile?
  @Published var takes = [Take]()
  @Published var selected = 0
  var take: Take? { takes.indices.contains(selected) ? takes[selected] : nil }
  func clearTakes() {
    player?.stop()
    takes.removeAll()
    selected = 0
  }
  func use(_ url: URL, asDrums: Bool) -> Bool {
    guard url.isFileURL, ["mid", "midi"].contains(url.pathExtension.lowercased()) else {
      status = "標準MIDIファイル（.mid / .midi）を選んでください"
      return false
    }
    if asDrums { drums = url } else { melody = url }
    status = ""
    return true
  }
  @Published var player: AVAudioPlayer?
  @Published var busy = false
  @Published var status = ""
  func perform(_ job: @escaping @MainActor () async throws -> Void) {
    busy = true
    status = ""
    player?.stop()
    Task { @MainActor in
      defer { busy = false }
      do { try await job() } catch { status = error.localizedDescription }
    }
  }
  func pick() -> URL? {
    let panel = NSOpenPanel()
    panel.allowedContentTypes = [.midi]
    return panel.runModal() == .OK ? panel.url : nil
  }
  func generate() async throws {
    guard let melody else { return }
    let fields = kickText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
    let kicks = fields.compactMap(Int.init)
    guard kicks.count == fields.count, kicks.allSatisfy({ (0...127).contains($0) }) else {
      throw NSError(
        domain: "Merlai", code: 1,
        userInfo: [NSLocalizedDescriptionKey: "キックは0〜127の番号をカンマで区切ってください"])
    }
    let dir = FileManager.default.temporaryDirectory.appendingPathComponent(
      "Merlai-" + UUID().uuidString)
    let req = Request(
      melody: melody.path, drums: drums?.path, output: dir.path, bars: bars, seed: takes.count, kicks: kicks,
      tonic: tonic < 0 ? nil : tonic, attack_ms: profile?.attack_ms ?? 0,
      release_ms: profile?.release_ms ?? 0)
    let data = try await helper("merlai-compose", [], input: JSONEncoder().encode(req))
    let result = try JSONDecoder().decode(Response.self, from: data)
    try data.write(to: dir.appendingPathComponent("song.json"), options: .atomic)
    takes.append(
      Take(
        directory: dir, candidates: result.candidates, voice: instrument,
        drumVoice: drums == nil ? "" : drumInstrument))
    selected = takes.count - 1
  }
  func restoreProfile() async {
    guard !instrument.isEmpty else {
      profile = nil
      return
    }
    do {
      let data = try await helper("Host", ["profile", instrument])
      profile = try JSONDecoder().decode(Profile.self, from: data)
    } catch {
      profile = nil
    }
  }
  func preview(_ index: Int) async throws {
    guard let take else { return }
    let session = take.directory
    let url = session.appendingPathComponent("preview-\(index).caf")
    if !FileManager.default.fileExists(atPath: url.path) {
      let temporary = session.appendingPathComponent(UUID().uuidString + ".caf")
      defer { try? FileManager.default.removeItem(at: temporary) }
      var arguments = [
        "render", take.voice, session.appendingPathComponent("song.json").path, String(index),
        temporary.path,
      ]
      if !take.drumVoice.isEmpty { arguments.append(take.drumVoice) }
      _ = try await helper("Host", arguments)
      try FileManager.default.moveItem(at: temporary, to: url)
    }
    player = try AVAudioPlayer(contentsOf: url)
    player?.play()
  }
}
struct Composer: View {
  @StateObject private var model = ComposerModel()
  var body: some View {
    VStack(alignment: .leading, spacing: 14) {
      HStack {
        Button("メロディーMIDIを開く") { if let url = model.pick() { _ = model.use(url, asDrums: false) } }
        Text(model.melody?.lastPathComponent ?? "未選択")
      }
      .frame(maxWidth: .infinity, alignment: .leading)
      .contentShape(Rectangle())
      .dropDestination(for: URL.self) { urls, _ in
        guard !model.busy, urls.count == 1, let url = urls.first else { return false }
        return model.use(url, asDrums: false)
      }
      HStack {
        Button("ドラムMIDIを開く") { if let url = model.pick() { _ = model.use(url, asDrums: true) } }
        Text(model.drums?.lastPathComponent ?? "任意")
        if model.drums != nil { Button("外す") { model.drums = nil } }
      }
      .frame(maxWidth: .infinity, alignment: .leading)
      .contentShape(Rectangle())
      .dropDestination(for: URL.self) { urls, _ in
        guard !model.busy, urls.count == 1, let url = urls.first else { return false }
        return model.use(url, asDrums: true)
      }
      if model.drums != nil {
        Picker("ドラム音源", selection: $model.drumInstrument) {
          Text("試聴しない").tag("")
          ForEach(model.instruments) { Text($0.name).tag($0.id) }
        }
        .onChange(of: model.drumInstrument) { _, _ in
          UserDefaults.standard.set(model.drumInstrument, forKey: "drumInstrument")
          model.clearTakes()
        }
      }
      HStack {
        Text("キック番号")
        TextField("36,37", text: $model.kickText)
        Stepper("\(model.bars)小節", value: $model.bars, in: 1...16)
      }
      Picker("主音", selection: $model.tonic) {
        Text("メロディーの先頭音").tag(-1)
        ForEach(0..<12) { i in
          Text(["C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B"][i]).tag(i)
        }
      }
      Picker("音源", selection: $model.instrument) {
        Text("MIDIのみ").tag("")
        ForEach(model.instruments) { Text($0.name).tag($0.id) }
      }
      .onChange(of: model.instrument) { _, _ in
        UserDefaults.standard.set(model.instrument, forKey: "instrument")
        model.profile = nil
        model.clearTakes()
        Task { await model.restoreProfile() }
      }
      HStack {
        Button("音色を選んで計測") {
          model.perform {
            let data = try await helper("Host", ["configure", model.instrument])
            model.profile = try JSONDecoder().decode(Profile.self, from: data)
            model.clearTakes()
          }
        }.disabled(model.instrument.isEmpty)
        if let profile = model.profile {
          Text(
            "\(profile.tag) 立ち上がり \(Int(profile.attack_ms)) ms ／ 余韻 \(Int(profile.release_ms)) ms（保存済み音色）")
        }
      }
      Button(model.takes.isEmpty ? "続きを3案生成" : "別テイクを生成") { model.perform { try await model.generate() } }.disabled(
        model.melody == nil)
      if !model.takes.isEmpty {
        Picker("テイク", selection: $model.selected) {
          ForEach(model.takes.indices, id: \.self) { index in
            Text("テイク \(index + 1)").tag(index)
          }
        }.onChange(of: model.selected) { _, _ in model.player?.stop() }
      }
      ForEach(Array((model.take?.candidates ?? []).enumerated()), id: \.element.id) { index, item in
        HStack {
          Button("試聴") { model.perform { try await model.preview(index) } }.disabled(
            model.take?.voice.isEmpty != false)
          Text("候補 \(index+1) をLogicへドラッグ").onDrag {
            midiProvider(item.file)
          }
          Button("Finderで表示") {
            NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: item.file)])
          }
        }
      }
      if model.busy { ProgressView().controlSize(.small) }
      Text(model.status).foregroundStyle(.secondary).textSelection(.enabled)
    }.padding(24).frame(minWidth: 510).disabled(model.busy)
      .onChange(of: model.melody) { _, _ in model.clearTakes() }
      .onChange(of: model.drums) { _, _ in model.clearTakes() }
      .task {
        do {
          model.instruments = try JSONDecoder().decode(
            [Instrument].self, from: await helper("Host", ["list"])
          ).sorted { $0.name < $1.name }
          if !model.instrument.isEmpty,
            !model.instruments.contains(where: { $0.id == model.instrument })
          {
            model.instrument = ""
          }
          if !model.drumInstrument.isEmpty,
            !model.instruments.contains(where: { $0.id == model.drumInstrument })
          {
            model.drumInstrument = ""
          }
          await model.restoreProfile()
        } catch { model.status = error.localizedDescription }
      }
  }
}
@main struct MerlaiApp: App {
  var body: some Scene { Window("Merlai", id: "composer") { Composer() } }
}
