//
//  ProjectDetailView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct ProjectDetailView: View {
    @EnvironmentObject var projectStore: ProjectStore
    
    var body: some View {
        VStack(alignment: .center) {
            Text("Project information")
                .font(.title3)
            Divider()
            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
                GridRow {
                    Text("Name")
                        .bold()
                    Text(projectStore.project.name)
                }
                GridRow {
                    Text("Path")
                        .bold()
                    LocalFileLinkButton(path: projectStore.project.path)
                }
                GridRow {
                    Text("Configuration")
                        .bold()
                    Text(projectStore.project.configurations.map { resource in
                        resource.name
                    }.joined(separator: ", "))
                }
                GridRow {
                    Text("Targets")
                        .bold()
                    Text(projectStore.project.targets.map { resource in
                        resource.name
                    }.joined(separator: ", "))
                }
                GridRow {
                    Text("Schemes")
                        .bold()
                    Text(projectStore.project.schemes.map { resource in
                        resource.name
                    }.joined(separator: ", "))
                }
            }
            Spacer()
        }.padding()
    }
}

#Preview {
    ProjectDetailView()
        .environmentObject(ProjectStore(project: Components.Schemas.XcProjectPublic.mock))
}
