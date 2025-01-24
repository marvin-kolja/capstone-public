//
//  BuildsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildsView: View {
    @EnvironmentObject var buildsStore: BuildsStore
    
    @State private var selection: Components.Schemas.BuildPublic?
    
    var body: some View {
        TwoColumnView(content: {
            List(buildsStore.builds, id: \.id, selection: $selection) { build in
                Text(build.id)
                    .tag(build)
            }
            .listStyle(.sidebar)
            .scrollContentBackground(.hidden)
        }, detail: {
            if let build = selection {
                BuildDetailView(build: build)
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
