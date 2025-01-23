//
//  ProjectView.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import SwiftUI

struct ProjectView: View {
    var project: Components.Schemas.XcProjectPublic
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            keyValueRow(title: "Name:", value: project.name)
            keyValueRow(title: "Path:", value: project.path)
            
            listRow(title: "Configurations:", items: project.configurations.map { $0.name })
            listRow(title: "Targets:", items: project.targets.map { $0.name })
            listRow(title: "Schemes:", items: project.schemes.map { $0.name })
            
            let testPlans = project.schemes.flatMap { scheme in
                scheme.xcTestPlans.map { "\($0.name) (\(scheme.name))" }
            }
            listRow(title: "Test Plans:", items: testPlans)
        }
        .padding()
    }
    
    private func keyValueRow(title: String, value: String) -> some View {
        HStack(alignment: .top) {
            Text(title)
                .frame(width: 120, alignment: .trailing)
                .font(.headline)
                .lineLimit(1)
            Text(value)
                .frame(maxWidth: .infinity, alignment: .leading)
                .lineLimit(1)
        }
    }
    
    private func listRow(title: String, items: [String]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .top) {
                Text(title)
                    .frame(width: 120, alignment: .trailing)
                    .font(.headline)
                    .lineLimit(1)
                VStack(alignment: .leading) {
                    if items.isEmpty {
                        Text("None")
                    } else {
                        ForEach(items, id: \.self) { item in
                            Text(item)
                                .lineLimit(1)
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    ProjectView(project: Components.Schemas.XcProjectPublic.mock)
}
