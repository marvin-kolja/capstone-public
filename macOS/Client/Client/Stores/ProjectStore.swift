//
//  ProjectStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

@MainActor
class ProjectStore: ObservableObject {
    @Published var project: Components.Schemas.XcProjectPublic
    
    init(project: Components.Schemas.XcProjectPublic) {
        self.project = project
    }
}
