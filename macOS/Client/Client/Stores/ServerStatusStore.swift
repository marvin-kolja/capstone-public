//
//  ServerStatusStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation
import Combine

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
    
    /// Stores the subscription for succesfull api calls, otherwise it would be disposed directly
    private var cancellables = Set<AnyCancellable>()
    private var checkScheduled = false
    
    init(apiClient: APIClientProtocol) {
        self.apiClient = apiClient
        
        Task {
            await self.checkHealth()
        }
        
        if let apiClient = apiClient as? APIClient {
            apiClient.apiCallSuccessSubject
                .sink { [weak self] success in
                    logger.debug("Got new apiCallSuccessSubject event, sucess: \(success)")
                    
                    guard let self = self else { return }
                    
                    switch self.serverStatus {
                    case .healthy:
                        if !success {
                            // If current status is healthy, but request failed, check immediately
                            Task {
                                await self.checkHealth()
                            }
                        }
                    default:
                        if success {
                            // If current status is not healthy, but request succesful, check immediately
                            Task {
                                await self.checkHealth()
                            }
                        }
                        // Always schedule a check when server status is not healthy
                        self.tryScheduleNextCheck(inSeconds: 10)
                    }
                }
                .store(in: &cancellables)
        }
    }
    
    func checkHealth() async {
        guard !checkingHealth else {
            logger.debug("Already checking server health")
            return
        }
        
        checkingHealth = true
        
        defer { checkingHealth = false }
        
        do {
            logger.debug("Checking server health")
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
            logger.debug("AppError checking server health \(appError.type)")
            serverStatus = .down(error: appError)
            tunnelConnectStatus = .unknown
            dbStatus = .unknown
        } catch {
            logger.debug("Unexpected error checking server health \(error)")
            serverStatus = .down(error: AppError(type: ServerHealthCheckError.unexpected))
            tunnelConnectStatus = .unknown
            dbStatus = .unknown
        }
    }
    
    /// This will schedule a new check in the given `inSeconds` seconds when no check is scheduled already
    private func tryScheduleNextCheck(inSeconds: Double) {
        guard !checkScheduled else {
            logger.debug("Sever health check already scheduled")
            return
        }
        
        checkScheduled = true
        
        logger.debug("Schedule next check")
        DispatchQueue.main.asyncAfter(deadline: .now() + inSeconds) { [weak self] in
            self?.checkScheduled = false
            Task {
                await self?.checkHealth()
            }
        }
    }
}
