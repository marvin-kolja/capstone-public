//
//  SessionsStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

@MainActor
class SessionsStore: ProjectContext {
    @Published var sessions: [Components.Schemas.TestSessionPublic] = []
    
    // TODO: Add methods to manipulate data
}
