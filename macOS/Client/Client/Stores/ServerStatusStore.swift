//
//  ServerStatusStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

enum ServerHealthCheckError: LocalizedError {
    case unexpected
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "An unexpected error checking the server health"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        }
    }
}

enum ServerStatus {
    case healthy
    case unhealty
    case down(error: AppError?)
    case unknown
}

/// Observable object that store the server health, error, and if it's currently checking the server health.
@MainActor
class ServerStatusStore: ObservableObject {
    @Published var checkingHealth = false
    @Published var serverStatus: ServerStatus = .unknown
    @Published var dbStatus: ServerStatus = .unknown
    @Published var tunnelConnectStatus: ServerStatus = .unknown
    
    private let apiClient: APIClientProtocol
    private var timer: Timer?
    
    init(apiClient: APIClientProtocol) {
        self.apiClient = apiClient
    }
    
    func checkHealth() async {
        guard !checkingHealth else {
            return
        }
        
        checkingHealth = true
        
        defer { checkingHealth = false }
        
        do {
            let serverHealth = try await apiClient.healthCheck()
            
            switch serverHealth.status {
            case .ok:
                serverStatus = .healthy
            case .unhealthy:
                serverStatus = .unhealty
            }
            switch serverHealth.tunnelConnect {
            case .ok:
                tunnelConnectStatus = .healthy
            case .unavailable:
                tunnelConnectStatus = .unhealty
            }
            switch serverHealth.db {
            case .ok:
                dbStatus = .healthy
            case .unavailable:
                dbStatus = .unhealty
            }
        } catch let appError as AppError {
            serverStatus = .down(error: appError)
            tunnelConnectStatus = .unknown
            dbStatus = .unknown
        } catch {
            serverStatus = .down(error: AppError(type: ServerHealthCheckError.unexpected))
            tunnelConnectStatus = .unknown
            dbStatus = .unknown
        }
    }
    
    /// This will also monitor the server health every `monitoringInterval` seconds.
    ///
    /// If already monitoring this will just return.
    func startMonitoring(interval: Double) {
        guard timer == nil else {
            return
        }
        
        Task {
            await self.checkHealth()
        }
        
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
              Task {
                  await self?.checkHealth()
              }
        }
    }
    
    deinit {
        timer?.invalidate()
        timer = nil
    }
}
