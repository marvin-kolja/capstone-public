//
//  AppState.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import Foundation

@MainActor
class AppState: ObservableObject {
    @Published var isConnectedToServer = false
    @Published var checkingConnection = false
    
    private let apiClient: APIClientProtocol
    
    init(apiClient: APIClientProtocol) {
        self.apiClient = apiClient
        
        Task {
            await self.checkConnection()
        }
    }
    
    func checkConnection() async {
        guard !checkingConnection else {
            return
        }
        
        checkingConnection = true
        
        defer { checkingConnection = false }
        
        let isConnected = await apiClient.checkConnection()
        
        
        checkingConnection = false
        isConnectedToServer = isConnected
    }
}
