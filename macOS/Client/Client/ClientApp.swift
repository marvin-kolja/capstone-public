//
//  ClientApp.swift
//  Client
//
//  Created by Marvin Willms on 29.10.24.
//

import SwiftData
import SwiftUI

@main
struct ClientApp: App {
    @StateObject private var projectStore: ProjectStore
    @StateObject private var serverStatusStore: ServerStatusStore
    @StateObject private var deviceStore: DeviceStore

    private var apiClient: APIClientProtocol

    init() {
        do {
            let apiClient: APIClientProtocol
            if ProcessInfo.processInfo.environment["USE_API_MOCK_CLIENT"] == "TRUE" {
                apiClient = MockAPIClient()
            } else {
                apiClient = try APIClient()
            }
            self.apiClient = apiClient
            _projectStore = StateObject(wrappedValue: ProjectStore(apiClient: apiClient))
            _serverStatusStore = StateObject(wrappedValue: ServerStatusStore(apiClient: apiClient))
            _deviceStore = StateObject(wrappedValue: DeviceStore(apiClient: apiClient))
        } catch {
            fatalError("Failed to intiialize API Client: \(error)")
        }
    }

    var body: some Scene {
        Window("Welcome to Capstone", id: "main") {
            WelcomeContentView()
                .environmentObject(projectStore)
                .environmentObject(serverStatusStore)
                .frame(minWidth: 800, maxWidth: 800, minHeight: 500, maxHeight: 500)
                .onAppear(perform: {
                    DispatchQueue.main.async {
                        NSApplication.shared.windows.forEach { window in
                            window.standardWindowButton(.zoomButton)?.isEnabled = false
                            window.standardWindowButton(.miniaturizeButton)?.isEnabled = false
                        }
                    }
                })
        }
        .windowResizability(.contentSize)
        .defaultPosition(.center)

        WindowGroup(for: Components.Schemas.XcProjectPublic.self) { $project in
            if let project = project {
                ProjectContentView(project: project, apiClient: apiClient)
                    .environmentObject(serverStatusStore)
                    .environmentObject(deviceStore)
                    .frame(minWidth: 800, minHeight: 500)
                    .navigationTitle(project.name)
                    .onAppear(perform: {
                        NSWindow.allowsAutomaticWindowTabbing = false
                    })
            }
        }
        .defaultPosition(.center)
        .commands {
            CommandGroup(replacing: CommandGroupPlacement.newItem) {}
        }
    }
}
