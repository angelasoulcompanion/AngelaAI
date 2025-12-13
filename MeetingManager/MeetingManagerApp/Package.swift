// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "MeetingManagerApp",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "MeetingManagerApp",
            targets: ["MeetingManagerApp"]
        )
    ],
    dependencies: [
        // PostgreSQL Client
        .package(url: "https://github.com/codewinsdotcom/PostgresClientKit.git", from: "1.4.0")
    ],
    targets: [
        .executableTarget(
            name: "MeetingManagerApp",
            dependencies: [
                .product(name: "PostgresClientKit", package: "PostgresClientKit")
            ],
            path: "Sources"
        )
    ]
)
