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
    var project: Components.Schemas.XcProjectPublic
    
    @EnvironmentObject var serverStatusStore: ServerStatusStore
    
    @State private var visibility: NavigationSplitViewVisibility = .doubleColumn
    @State private var selection: Selection = .general
    
    var body: some View {
        NavigationSplitView(columnVisibility: $visibility) {
            List(Selection.allCases, selection: $selection) { item in
                Label(item.title, systemImage: icon(for: item))
                    .tag(item)
            }
            .listStyle(.sidebar)
            .navigationTitle("Project")
        } detail: {
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
    ProjectView(project: Components.Schemas.XcProjectPublic.mock)
        .environmentObject(ServerStatusStore(apiClient: MockAPIClient()))
}
