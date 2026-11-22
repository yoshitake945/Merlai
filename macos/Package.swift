// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "MerlaiNative", platforms: [.macOS(.v14)], targets: [
    .executableTarget(name: "Merlai"),
    .systemLibrary(name: "CSQLite"),
    .executableTarget(name: "Host", dependencies: ["CSQLite"])
])
