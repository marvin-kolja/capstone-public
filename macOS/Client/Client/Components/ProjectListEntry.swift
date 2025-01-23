//
//  ProjectListEntry.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import SwiftUI

struct ProjectListEntry: View {
    var project: Components.Schemas.XcProjectPublic
    @State private var isHovered = false
    
    var body: some View {
        VStack(alignment: .leading) {
            Text(project.name)
                .bold()
                .frame( maxWidth: .infinity, alignment: .leading)
            Text(project.path)
                .lineLimit(1)
                .truncationMode(.head)
                .frame( maxWidth: .infinity, alignment: .leading)
        }
        .frame( maxWidth: .infinity)
        .padding(.all)
        .background(isHovered ? .accentColor : Color.clear)
        .cornerRadius(8)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

#Preview {
    ProjectListEntry(project: Components.Schemas.XcProjectPublic.mock)
}
