//
//  ProjectContentView.swift
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

struct ProjectContentView: View {
    @EnvironmentObject var serverStatusStore: ServerStatusStore
    @EnvironmentObject private var devicesStore: DeviceStore

    @StateObject private var buildsStore: BuildStore
    @StateObject private var currentProjectStore: CurrentProjectStore
    @StateObject private var testPlanStore: TestPlanStore
    @StateObject private var sessionStore: SessionStore

    @State private var visibility: NavigationSplitViewVisibility = .doubleColumn
    @State private var selection: Selection = .general

    init(project: Components.Schemas.XcProjectPublic, apiClient: APIClientProtocol) {
        _currentProjectStore = StateObject(wrappedValue: CurrentProjectStore(project: project))
        _buildsStore = StateObject(
            wrappedValue: BuildStore(projectId: project.id, apiClient: apiClient))
        _testPlanStore = StateObject(
            wrappedValue: TestPlanStore(projectId: project.id, apiClient: apiClient))
        _sessionStore = StateObject(
            wrappedValue: SessionStore(projectId: project.id, apiClient: apiClient))
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
                Divider().padding(0)
                HStack {
                    Spacer()
                    ManageDevicesButton()
                        .padding(0)
                }
                .padding(.bottom, 8)
                .padding(.horizontal, 8)
            }
            .environmentObject(currentProjectStore)
            .environmentObject(buildsStore)
            .environmentObject(testPlanStore)
            .environmentObject(sessionStore)
        }
        .task { await devicesStore.loadDevices() }
        .toolbar {
            ToolbarItem(placement: .status) {
                ServerStatusButton(
                    isLoading: serverStatusStore.checkingHealth,
                    serverStatus: serverStatusStore.serverStatus
                ) {
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
    ProjectContentView(project: Components.Schemas.XcProjectPublic.mock, apiClient: MockAPIClient())
        .environmentObject(ServerStatusStore(apiClient: MockAPIClient()))
}
