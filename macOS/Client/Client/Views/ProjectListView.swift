//
//  ProjectListView.swift
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


struct ProjectListView: View {
    @Environment(\.openWindow) private var openWindow
    @Environment(\.refresh) private var refresh
    
    @EnvironmentObject var projectsStore: ProjectsStore
    @EnvironmentObject var serverStatusStore: ServerStatusStore
    
    @State private var showFileImporter = false
    
    var body: some View {
        VStack {
            if projectsStore.projects.isEmpty {
                if projectsStore.loadingProjects {
                    ProgressView()
                        .controlSize(.small)
                        .accessibilityIdentifier("projects-list-progress-view")
                }
                if let error = projectsStore.errorLoadingProjects {
                    ErrorText(error: error)
                        .accessibilityIdentifier("projects-list-loading-error")
                } else {
                    Text("No projects found")
                        .accessibilityIdentifier("projects-list-no-projects")
                }
            } else {
                List(projectsStore.projects, id: \.id) { project in
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
        .task { await projectsStore.loadProjects() }
        .fileImporter(
            isPresented: $showFileImporter,
            allowedContentTypes: [.xcodeproj],
            allowsMultipleSelection: false
        ) { result in
            handleFileResult(result)
        }
        .toolbar {
            ToolbarItem(placement: .status) {
                ServerStatusButton(isLoading: serverStatusStore.checkingHealth, serverStatus: serverStatusStore.serverStatus) {
                    ServerStatusDetailView()
                }
                .accessibilityIdentifier("server-status")
            }
            ToolbarItem(placement: .automatic) {
                LoadingButton(isLoading: projectsStore.loadingProjects, action: {
                    Task {
                        await projectsStore.loadProjects()
                    }
                }) {
                    Image(systemName: "arrow.clockwise")
                }
                .accessibilityIdentifier("refresh-projects")
            }
            ToolbarItem(placement: .automatic) {
                LoadingButton(isLoading: projectsStore.addingProject, action: {
                    showFileImporter = true
                }) {
                    Image(systemName: "folder.badge.plus")
                }
                .accessibilityIdentifier("add-project")
            }
        }
        .alert(isPresented: $projectsStore.showAddingProjectError, withError: projectsStore.errorAddingProject)
    }
    
    func handleFileResult(_ result: Result<[URL], any Error>) {
        switch result {
        case .success(let urls):
            if let unwrappedURL: URL = urls.first {
                Task {
                    await projectsStore.addProject(url: unwrappedURL)
                }
            }
        case .failure(let error):
            print("Error selecting file \(error.localizedDescription)")
        }
        showFileImporter = false
    }
}

#Preview {
    ProjectListView().environmentObject(ProjectsStore(apiClient: MockAPIClient()))
}
