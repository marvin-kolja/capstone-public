//
//  ClientApp.swift
//  Client
//
//  Created by Marvin Willms on 29.10.24.
//

import SwiftUI
import SwiftData

@main
struct ClientApp: App {
    @StateObject private var projectsStore: ProjectsStore
    @StateObject private var serverStatusStore: ServerStatusStore
    @StateObject private var devicesStore: DevicesStore
    
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
            _projectsStore = StateObject(wrappedValue: ProjectsStore(apiClient: apiClient))
            _serverStatusStore = StateObject(wrappedValue: ServerStatusStore(apiClient: apiClient))
            _devicesStore = StateObject(wrappedValue: DevicesStore(apiClient: apiClient))
        } catch {
            fatalError("Failed to intiialize API Client: \(error)")
        }
    }
    
    var body: some Scene {
        Window("Welcome to Capstone", id: "main") {
            ProjectListView()
                .environmentObject(projectsStore)
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
                ProjectView(project: project, apiClient: apiClient)
                    .environmentObject(serverStatusStore)
                    .environmentObject(devicesStore)
                    .frame(minWidth: 800, minHeight: 500)
                    .navigationTitle(project.name)
                    .onAppear(perform: {
                        NSWindow.allowsAutomaticWindowTabbing = false
                    })
            }
        }
        .defaultPosition(.center)
        .commands {
            CommandGroup(replacing: CommandGroupPlacement.newItem) { }
        }
    }
}
