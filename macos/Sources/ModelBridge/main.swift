import Foundation

struct Failure: LocalizedError {
  let message: String
  var errorDescription: String? { message }
}

struct Model: Codable { let id: String; let displayName: String }
struct Provider: Codable {
  let id: String
  let displayName: String
  let kind: String
  let locality: String
  let available: Bool
  let models: [Model]
  let detail: String
}
struct Note: Codable {
  let start, end: Double
  let pitch, velocity, channel: Int
}
struct MusicalContext: Codable {
  let span: Double
  let tempo: Double?
  let timeSignature: String?
  let source: String?
  let sourceId: UInt64?
  let sourceRevision: UInt64?
  let sourceKind: String?
}
struct GenerationPayload: Codable {
  let version: Int
  let instruction, purpose: String
  let musicalContext: MusicalContext
  let notes: [Note]
}
struct GenerateRequest: Codable {
  let providerId, model: String
  let endpoint: String?
  let payload: GenerationPayload
}
struct GenerationResponse: Codable {
  let notes: [Note]
}

func executable(_ name: String) -> String? {
  let paths = (ProcessInfo.processInfo.environment["PATH"] ?? "").split(separator: ":")
  if let found = paths.map({ URL(fileURLWithPath: String($0)).appendingPathComponent(name).path })
    .first(where: { FileManager.default.isExecutableFile(atPath: $0) }) { return found }
  let extensions = FileManager.default.homeDirectoryForCurrentUser
    .appendingPathComponent(".vscode/extensions")
  guard let entries = try? FileManager.default.contentsOfDirectory(
    at: extensions, includingPropertiesForKeys: nil) else { return nil }
  for entry in entries where entry.lastPathComponent.lowercased().contains(name == "codex" ? "openai" : name) {
    let bin = entry.appendingPathComponent("bin")
    guard let platforms = try? FileManager.default.contentsOfDirectory(at: bin, includingPropertiesForKeys: nil)
    else { continue }
    for platform in platforms {
      let candidate = platform.appendingPathComponent(name).path
      if FileManager.default.isExecutableFile(atPath: candidate) { return candidate }
    }
  }
  return nil
}

func http(_ request: URLRequest, timeout: TimeInterval = 2) throws -> Data {
  let semaphore = DispatchSemaphore(value: 0)
  var result: Result<Data, Error>?
  let configuration = URLSessionConfiguration.ephemeral
  configuration.timeoutIntervalForRequest = timeout
  let task = URLSession(configuration: configuration).dataTask(with: request) { data, response, error in
    if let error { result = .failure(error) }
    else if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
      result = .failure(Failure(message: "HTTP \(http.statusCode)"))
    } else { result = .success(data ?? Data()) }
    semaphore.signal()
  }
  task.resume()
  guard semaphore.wait(timeout: .now() + timeout + 1) == .success, let result else {
    task.cancel()
    throw Failure(message: "Model provider timed out")
  }
  return try result.get()
}

func localModels(_ endpoint: String) -> [Model] {
  guard let url = URL(string: endpoint + "/v1/models"),
    let data = try? http(URLRequest(url: url)),
    let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
    let entries = object["data"] as? [[String: Any]]
  else { return [] }
  return entries.compactMap { entry in
    (entry["id"] as? String).map { Model(id: $0, displayName: $0) }
  }
}

func providers(manualEndpoint: String?) -> [Provider] {
  let codex = executable("codex")
  let claude = executable("claude")
  var result = [
    Provider(id: "codex", displayName: "Codex CLI", kind: "cli", locality: "cloud",
      available: codex != nil, models: [], detail: codex ?? "codex が見つかりません"),
    Provider(id: "claude", displayName: "Claude CLI", kind: "cli", locality: "cloud",
      available: claude != nil, models: [], detail: claude ?? "claude が見つかりません"),
  ]
  for (id, name, endpoint) in [
    ("ollama", "Ollama", "http://127.0.0.1:11434"),
    ("lmstudio", "LM Studio", "http://127.0.0.1:1234"),
  ] {
    let models = localModels(endpoint)
    result.append(Provider(id: id, displayName: name, kind: "openai_compatible",
      locality: "local", available: !models.isEmpty, models: models,
      detail: models.isEmpty ? "\(endpoint) に接続できません" : endpoint))
  }
  if let endpoint = manualEndpoint, !endpoint.isEmpty {
    let clean = endpoint.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    let models = localModels(clean)
    result.append(Provider(id: "custom", displayName: "ローカル互換API", kind: "openai_compatible",
      locality: "local", available: !models.isEmpty, models: models,
      detail: models.isEmpty ? "\(clean) に接続できません" : clean))
  }
  return result
}

func run(_ path: String, _ arguments: [String], input: Data, timeout: TimeInterval = 120) throws -> Data {
  let process = Process()
  process.executableURL = URL(fileURLWithPath: path)
  process.arguments = arguments
  process.currentDirectoryURL = FileManager.default.temporaryDirectory
  let stdin = Pipe()
  let outputURL = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
  let errorURL = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
  FileManager.default.createFile(atPath: outputURL.path, contents: nil)
  FileManager.default.createFile(atPath: errorURL.path, contents: nil)
  defer {
    try? FileManager.default.removeItem(at: outputURL)
    try? FileManager.default.removeItem(at: errorURL)
  }
  let stdout = try FileHandle(forWritingTo: outputURL)
  let stderr = try FileHandle(forWritingTo: errorURL)
  defer { try? stdout.close(); try? stderr.close() }
  process.standardInput = stdin
  process.standardOutput = stdout
  process.standardError = stderr
  try process.run()
  stdin.fileHandleForWriting.write(input)
  try stdin.fileHandleForWriting.close()
  let deadline = Date().addingTimeInterval(timeout)
  while process.isRunning && Date() < deadline { Thread.sleep(forTimeInterval: 0.05) }
  if process.isRunning { process.terminate(); throw Failure(message: "Model provider timed out") }
  try? stdout.synchronize()
  try? stderr.synchronize()
  let output = try Data(contentsOf: outputURL)
  guard process.terminationStatus == 0 else {
    let message = (try? String(contentsOf: errorURL, encoding: .utf8)) ?? ""
    throw Failure(message: diagnosticSummary(message))
  }
  return output
}

func diagnosticSummary(_ diagnostic: String) -> String {
  if diagnostic.contains("invalid_json_schema") { return "モデルが出力形式を拒否しました。Merlaiを更新してください。" }
  if diagnostic.localizedCaseInsensitiveContains("login") ||
    diagnostic.localizedCaseInsensitiveContains("unauthorized") || diagnostic.contains("401") {
    return "モデルへログインできていません。CLIのログイン状態を確認してください。"
  }
  if diagnostic.localizedCaseInsensitiveContains("timed out") {
    return "モデルの応答がタイムアウトしました。再試行してください。"
  }
  let errors = diagnostic.split(separator: "\n").map(String.init)
    .filter { $0.hasPrefix("ERROR:") }
  if let last = errors.last {
    let value = String(last.dropFirst("ERROR:".count)).trimmingCharacters(in: .whitespaces)
    if let data = value.data(using: .utf8),
      let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
      let error = object["error"] as? [String: Any], let message = error["message"] as? String {
      return String(message.prefix(300))
    }
    return String(value.prefix(300))
  }
  return "モデルの実行に失敗しました。再試行するか、内蔵ルールを選んでください。"
}

let schema = #"{"type":"object","properties":{"notes":{"type":"array","items":{"type":"object","properties":{"start":{"type":"number"},"end":{"type":"number"},"pitch":{"type":"integer"},"velocity":{"type":"integer"},"channel":{"type":"integer"}},"required":["start","end","pitch","velocity","channel"],"additionalProperties":false}}},"required":["notes"],"additionalProperties":false}"#

func validateStrictSchema(_ value: Any) -> Bool {
  guard let object = value as? [String: Any] else { return true }
  if let properties = object["properties"] as? [String: Any] {
    guard Set(object["required"] as? [String] ?? []) == Set(properties.keys) else { return false }
    if !properties.values.allSatisfy(validateStrictSchema) { return false }
  }
  if let items = object["items"], !validateStrictSchema(items) { return false }
  return true
}

func selfTest() throws {
  let value = try JSONSerialization.jsonObject(with: Data(schema.utf8))
  guard validateStrictSchema(value) else { throw Failure(message: "Model schema is not strict") }
  _ = try JSONDecoder().decode(GenerationResponse.self, from:
    Data(#"{"notes":[{"start":0,"end":0.5,"pitch":60,"velocity":80,"channel":0}]}"#.utf8))
}

func prompt(_ payload: GenerationPayload) throws -> Data {
  let data = try JSONEncoder().encode(payload)
  let json = String(decoding: data, as: UTF8.self)
  return Data(("You are a MIDI phrase editor. Return only JSON matching the supplied schema. " +
    "Keep every note inside musicalContext.span and MIDI ranges. " +
    "For edit, preserve the source unless the instruction requests a change. " +
    "For bass, chords, or counter_melody, create that role using the source as musical context. Request:\n" + json).utf8)
}

func generate(_ request: GenerateRequest) throws -> GenerationResponse {
  let input = try prompt(request.payload)
  let raw: Data
  switch request.providerId {
  case "codex":
    guard let path = executable("codex") else { throw Failure(message: "codex が見つかりません") }
    let schemaURL = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".json")
    try Data(schema.utf8).write(to: schemaURL, options: .atomic)
    defer { try? FileManager.default.removeItem(at: schemaURL) }
    let outputURL = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".json")
    defer { try? FileManager.default.removeItem(at: outputURL) }
    var args = ["exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
      "--output-schema", schemaURL.path, "--output-last-message", outputURL.path]
    if !request.model.isEmpty { args += ["--model", request.model] }
    args.append("-")
    _ = try run(path, args, input: input)
    raw = try Data(contentsOf: outputURL)
  case "claude":
    guard let path = executable("claude") else { throw Failure(message: "claude が見つかりません") }
    var args = ["--print", "--output-format", "json", "--json-schema", schema]
    if !request.model.isEmpty { args += ["--model", request.model] }
    let envelope = try run(path, args, input: input)
    if let object = try JSONSerialization.jsonObject(with: envelope) as? [String: Any],
      let value = object["structured_output"] ?? object["result"] {
      raw = try JSONSerialization.data(withJSONObject: value)
    } else { raw = envelope }
  default:
    let endpoint: String
    switch request.providerId {
    case "ollama": endpoint = "http://127.0.0.1:11434"
    case "lmstudio": endpoint = "http://127.0.0.1:1234"
    default: endpoint = request.endpoint ?? ""
    }
    guard let url = URL(string: endpoint.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + "/v1/chat/completions") else {
      throw Failure(message: "ローカルAPIのURLが不正です")
    }
    var urlRequest = URLRequest(url: url)
    urlRequest.httpMethod = "POST"
    urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
    urlRequest.httpBody = try JSONSerialization.data(withJSONObject: [
      "model": request.model,
      "messages": [["role": "user", "content": String(decoding: input, as: UTF8.self)]],
      "response_format": ["type": "json_object"],
      "stream": false,
    ])
    let envelope = try http(urlRequest, timeout: 120)
    let object = try JSONSerialization.jsonObject(with: envelope) as? [String: Any]
    guard let choices = object?["choices"] as? [[String: Any]],
      let message = choices.first?["message"] as? [String: Any],
      let content = message["content"] as? String
    else { throw Failure(message: "モデル応答を読み取れません") }
    raw = Data(content.utf8)
  }
  return try JSONDecoder().decode(GenerationResponse.self, from: raw)
}

do {
  let args = Array(CommandLine.arguments.dropFirst())
  switch args.first {
  case "providers":
    let endpoint = args.count > 1 ? args[1] : nil
    FileHandle.standardOutput.write(try JSONEncoder().encode(providers(manualEndpoint: endpoint)))
  case "generate":
    let data = FileHandle.standardInput.readDataToEndOfFile()
    FileHandle.standardOutput.write(try JSONEncoder().encode(generate(JSONDecoder().decode(GenerateRequest.self, from: data))))
  case "self-test":
    try selfTest()
    FileHandle.standardOutput.write(Data("ModelBridge self-test passed\n".utf8))
  default: throw Failure(message: "usage: ModelBridge providers [endpoint] | generate")
  }
} catch {
  FileHandle.standardError.write(Data((error.localizedDescription + "\n").utf8))
  exit(1)
}
