//
//  BuildStore.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import Foundation

enum StreamBuildUpdatesError: LocalizedError {
    case unexpected
    case invalidProjectId(projectId: String)
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to stream build updates"
        case .invalidProjectId:
            return "The given project id is invalid."
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidProjectId:
            return "Make sure the project id is valid"
        }
    }
}

enum StartBuildError: LocalizedError {
    case unexpected
    case invalidProjectId(projectId: String)
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to start a build"
        case .invalidProjectId:
            return "The given project id is invalid."
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidProjectId:
            return "Make sure the project id is valid"
        }
    }
}

class BuildStore: ProjectContext {
    @Published var build: Components.Schemas.BuildPublic
    
    @Published var startingBuild = false
    @Published var errorStartingBuild: AppError?
    
    @Published var streamingUpdates = false
    @Published var errorStreamingUpdates: AppError?
    
    init(projectId: String, apiClient: APIClientProtocol, build: Components.Schemas.BuildPublic) {
        _build = Published(initialValue: build)
        super.init(projectId: projectId, apiClient: apiClient)
    }
    
    func streamUpdates() async {
        guard !streamingUpdates else {
            return
        }
        
        streamingUpdates = true
        defer { streamingUpdates = false }
        
        do {
            let stream = try await apiClient.streamBuildUpdates(projectId: projectId, buildId: build.id)
            for try await newBuild in stream {
                build = newBuild
            }
        } catch let appError as AppError {
            if let apiError = appError.type as? APIError {
                switch apiError {
                case .clientRequestError:
                    errorStreamingUpdates = AppError(type: StreamBuildUpdatesError.invalidProjectId(projectId: projectId))
                default:
                    ()
                }
            }
            errorStreamingUpdates = appError
        } catch {
            errorStreamingUpdates = AppError(type: StreamBuildUpdatesError.unexpected)
        }
    }
    
    func startBuild() async {
        guard !startingBuild else {
            return
        }
        
        startingBuild = true
        defer { startingBuild = false }
        
        do {
            let requestData = Components.Schemas.StartBuildRequest(configuration: build.configuration, deviceId: build.deviceId, scheme: build.scheme, testPlan: build.testPlan)
            build = try await BuildStore.startBuild(projectId: projectId, data: requestData, apiClient: apiClient)
        } catch {
            guard error is AppError else {
                fatalError("Expected AppError")
            }
            errorStartingBuild = AppError(type: StartBuildError.unexpected)
        }
    }
    
    static func startBuild(projectId: String, data: Components.Schemas.StartBuildRequest, apiClient: APIClientProtocol) async throws -> Components.Schemas.BuildPublic {
        do {
            return try await apiClient.startBuild(projectId: projectId, data: data)
        } catch let appError as AppError {
            if let apiError = appError.type as? APIError {
                switch apiError {
                case .clientRequestError:
                    throw AppError(type: StartBuildError.invalidProjectId(projectId: projectId))
                default:
                    ()
                }
            }
            throw appError
        } catch {
            throw AppError(type: StartBuildError.unexpected)
        }
    }
}

extension BuildStore: Hashable {
    static func == (lhs: BuildStore, rhs: BuildStore) -> Bool {
        lhs.build == rhs.build
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(build)
    }
}

