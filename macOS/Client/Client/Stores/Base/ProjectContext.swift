//
//  ProjectContext.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

/// A base class for all stores that are project contextual. Meaning they are tied to a specific project (id).
class ProjectContext: APIClientContext {
    internal let projectId: String

    init(projectId: String, apiClient: APIClientProtocol) {
        self.projectId = projectId
        super.init(apiClient: apiClient)
    }
}
