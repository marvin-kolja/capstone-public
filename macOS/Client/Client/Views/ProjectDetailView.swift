//
//  ProjectDetailView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct ProjectDetailView: View {
    @EnvironmentObject var currentProjectStore: CurrentProjectStore
    
    var project: Components.Schemas.XcProjectPublic { currentProjectStore.project }
    
    var body: some View {
        VStack(alignment: .center) {
            Text("Project information")
                .font(.title3)
            Divider()
            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
                GridRow {
                    Text("Name")
                        .bold()
                    Text(project.name)
                }
                GridRow {
                    Text("Path")
                        .bold()
                    LocalFileLinkButton(path: project.path)
                }
                GridRow {
                    Text("Configuration")
                        .bold()
                    Text(project.configurations.map { resource in
                        resource.name
                    }.joined(separator: ", "))
                }
                GridRow {
                    Text("Targets")
                        .bold()
                    Text(project.targets.map { resource in
                        resource.name
                    }.joined(separator: ", "))
                }
                GridRow {
                    Text("Schemes")
                        .bold()
                    Text(project.schemes.map { resource in
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
        .environmentObject(CurrentProjectStore(project: Components.Schemas.XcProjectPublic.mock))
}
