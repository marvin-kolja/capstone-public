//
//  APIClientContext.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

/// A base class for all stores that use the apiClient.
@MainActor
class APIClientContext: ObservableObject {
    internal let apiClient: APIClientProtocol

    init(apiClient: APIClientProtocol) {
        self.apiClient = apiClient
    }
}
