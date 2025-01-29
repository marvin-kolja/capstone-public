//
//  WelcomeContentView.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import SwiftUI
import UniformTypeIdentifiers

struct ErrorText: View {
    var error: AppError

    var body: some View {
        VStack {
            Text(error.userMessage)
                .foregroundStyle(.red)
        }
    }
}

struct WelcomeContentView: View {
    @Environment(\.openWindow) private var openWindow
    @Environment(\.refresh) private var refresh

    @EnvironmentObject var projectStore: ProjectStore
    @EnvironmentObject var serverStatusStore: ServerStatusStore

    @State private var showFileImporter = false

    var body: some View {
        VStack {
            if projectStore.projects.isEmpty {
                if projectStore.loadingProjects {
                    ProgressView()
                        .controlSize(.small)
                        .accessibilityIdentifier("projects-list-progress-view")
                }
                if let error = projectStore.errorLoadingProjects {
                    ErrorText(error: error)
                        .accessibilityIdentifier("projects-list-loading-error")
                } else {
                    Text("No projects found")
                        .accessibilityIdentifier("projects-list-no-projects")
                }
            } else {
                List(projectStore.projects, id: \.id) { project in
                    HStack {
                        ProjectListEntry(project: project)
                    }.onTapGesture {
                        openWindow(value: project)
                    }
                }
                .nostyle()
            }
        }
        .padding()
        .frame(maxWidth: .infinity)
        .navigationTitle("Xcode Projects").accessibilityIdentifier("xcode-projects-list")
        .task { await projectStore.loadProjects() }
        .fileImporter(
            isPresented: $showFileImporter,
            allowedContentTypes: [.xcodeproj],
            allowsMultipleSelection: false
        ) { result in
            handleFileResult(result)
        }
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
            ToolbarItem(placement: .automatic) {
                LoadingButton(
                    isLoading: projectStore.loadingProjects,
                    action: {
                        Task {
                            await projectStore.loadProjects()
                        }
                    }
                ) {
                    Image(systemName: "arrow.clockwise")
                }
                .accessibilityIdentifier("refresh-projects")
            }
            ToolbarItem(placement: .automatic) {
                LoadingButton(
                    isLoading: projectStore.addingProject,
                    action: {
                        showFileImporter = true
                    }
                ) {
                    Image(systemName: "folder.badge.plus")
                }
                .accessibilityIdentifier("add-project")
            }
        }
        .alert(
            isPresented: $projectStore.showAddingProjectError,
            withError: projectStore.errorAddingProject)
    }

    func handleFileResult(_ result: Result<[URL], any Error>) {
        switch result {
        case .success(let urls):
            if let unwrappedURL: URL = urls.first {
                Task {
                    await projectStore.addProject(url: unwrappedURL)
                }
            }
        case .failure(let error):
            print("Error selecting file \(error.localizedDescription)")
        }
        showFileImporter = false
    }
}

#Preview {
    WelcomeContentView().environmentObject(ProjectStore(apiClient: MockAPIClient()))
}
