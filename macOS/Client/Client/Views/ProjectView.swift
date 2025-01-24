//
//  ProjectView.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import SwiftUI

enum Selection: String, CaseIterable, Identifiable {
    case general = "General"
    case builds = "Builds"
    case testPlans = "Test Plans"
    case sessions = "Sessions"

    var id: String { self.rawValue }
    var title: String { self.rawValue }
}

struct ProjectView: View {
    @EnvironmentObject var serverStatusStore: ServerStatusStore

    @StateObject private var projectStore: ProjectStore
    @StateObject private var buildsStore: BuildsStore

    @State private var visibility: NavigationSplitViewVisibility = .doubleColumn
    @State private var selection: Selection = .general

    init(project: Components.Schemas.XcProjectPublic, apiClient: APIClientProtocol) {
        _projectStore = StateObject(wrappedValue: ProjectStore(project: project))
        _buildsStore = StateObject(wrappedValue: BuildsStore(projectId: project.id, apiClient: apiClient))
    }

    var body: some View {
        NavigationSplitView(columnVisibility: $visibility) {
            List(Selection.allCases, selection: $selection) { item in
                Label(item.title, systemImage: icon(for: item))
                    .tag(item)
            }
            .listStyle(.sidebar)
            .navigationTitle("Project")
        } detail: {
            VStack {
                switch selection {
                case .general:
                    ProjectDetailView()
                case .builds:
                    BuildsView()
                case .testPlans:
                    TestPlansView()
                case .sessions:
                    SessionsView()
                }
            }
            .environmentObject(projectStore)
            .environmentObject(buildsStore)
        }
        .toolbar {
            ToolbarItem(placement: .status) {
                ServerStatusButton(isLoading: serverStatusStore.checkingHealth, serverStatus: serverStatusStore.serverStatus) {
                    ServerStatusDetailView()
                }
                .accessibilityIdentifier("server-status")
            }
        }
    }

    private func icon(for selection: Selection) -> String {
        switch selection {
        case .general: return "gearshape"
        case .builds: return "hammer"
        case .testPlans: return "doc.text.magnifyingglass"
        case .sessions: return "clock.arrow.circlepath"
        }
    }
}

#Preview {
    ProjectView(project: Components.Schemas.XcProjectPublic.mock, apiClient: MockAPIClient())
    .environmentObject(ServerStatusStore(apiClient: MockAPIClient()))
}
