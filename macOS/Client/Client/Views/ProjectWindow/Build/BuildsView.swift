//
//  BuildsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildsView: View {
    @EnvironmentObject var buildsStore: BuildStore

    @State private var isAddingItem: Bool = false
    @State private var selectedBuildId: String?

    var body: some View {
        TwoColumnView(
            content: {
                LoadingView(
                    isLoading: buildsStore.loadingBuilds, hasData: !buildsStore.builds.isEmpty,
                    refresh: {
                        Task {
                            await buildsStore.loadBuilds()
                        }
                    }
                ) {
                    ZStack {
                        List(buildsStore.builds, id: \.id, selection: $selectedBuildId) { build in
                            Text(build.userFriendlyName)
                                .tag(build.id)
                        }
                        .listStyle(.sidebar)
                        .scrollContentBackground(.hidden)
                        if buildsStore.builds.isEmpty {
                            Text("No Builds")
                        }
                    }
                }
            },
            detail: {
                if let buildId = selectedBuildId,
                    let build = buildsStore.getBuildById(buildId: buildId)
                {
                    BuildDetailView(build: build)
                } else {
                    Button("Add Build", action: { isAddingItem = true })
                }
            }
        )
        .task { await buildsStore.loadBuilds() }
        .toolbar {
            Button(action: { isAddingItem = true }) {
                Image(systemName: "plus")
            }
        }
        .sheet(isPresented: $isAddingItem) {
            AddBuildView()
        }
    }
}

#Preview {
    BuildsView()
        .environmentObject(
            BuildStore(
                projectId: Components.Schemas.BuildPublic.mock.projectId, apiClient: MockAPIClient()
            ))
}
