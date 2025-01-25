//
//  BuildsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildsView: View {
    @EnvironmentObject var buildsStore: BuildsStore

    @State private var isAddingItem: Bool = false
    @State private var selectedBuild: BuildStore?

    var body: some View {
        TwoColumnView(content: {
            LoadingView(isLoading: buildsStore.loadingBuilds, hasData: !buildsStore.buildStores.isEmpty, refresh: {
                Task {
                    await buildsStore.loadBuilds()
                }
            }) {
                ZStack {
                    List(buildsStore.buildStores, id: \.build.id, selection: $selectedBuild) { buildStore in
                        Text(buildStore.build.id)
                            .tag(buildStore)
                    }
                    .listStyle(.sidebar)
                    .scrollContentBackground(.hidden)
                    if (buildsStore.buildStores.isEmpty) {
                        Text("No Builds")
                    }
                }
            }
        }, detail: {
            if let buildStore = selectedBuild {
                BuildDetailView(buildStore: buildStore)
            } else {
                Button("Add Build", action: { isAddingItem = true })
            }
        })
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
        .environmentObject(BuildsStore(projectId: Components.Schemas.BuildPublic.mock.projectId, apiClient: MockAPIClient()))
}
