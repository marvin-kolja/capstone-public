//
//  SessionStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

@MainActor
class SessionStore: ProjectContext {
    @Published var sessions: [Components.Schemas.TestSessionPublic] = []
    
    // TODO: Add methods to manipulate data
}
