//
//  BuildsStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

class BuildsStore: ProjectContext {
    @Published var builds: [Components.Schemas.BuildPublic] = []
    
    // TODO: Add methods to manipulate data
}
