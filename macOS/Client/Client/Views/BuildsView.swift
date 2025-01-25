//
//  BuildsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildsView: View {
    @EnvironmentObject var buildsStore: BuildsStore
    
    var body: some View {
        TwoColumnView(content: {
            LoadingView(isLoading: buildsStore.loadingBuilds, hasData: !buildsStore.buildStores.isEmpty, refresh: {
                Task {
                    await buildsStore.loadBuilds()
                }
            }) {
                ZStack {
                    List(buildsStore.buildStores, id: \.build.id, selection: $buildsStore.selectedBuild) { buildStore in
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
            if let buildStore = buildsStore.selectedBuild {
                BuildDetailView(buildStore: buildStore)
            } else {
                EmptyView()
            }
        }).task { await buildsStore.loadBuilds() }
    }
}

#Preview {
    BuildsView()
        .environmentObject(BuildsStore(projectId: Components.Schemas.BuildPublic.mock.projectId, apiClient: MockAPIClient()))
}
