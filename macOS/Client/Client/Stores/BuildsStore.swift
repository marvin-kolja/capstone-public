//
//  BuildsStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

enum LoadBuildsError: LocalizedError {
    case unexpected
    case invalidProjectId(projectId: String)
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to load the builds."
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

class BuildsStore: ProjectContext {
    @Published var builds: [Components.Schemas.BuildPublic] = []
    
    @Published var loadingBuilds = false
    @Published var errorLoadingBuilds: AppError?
    
    func loadBuilds() async {
        guard !loadingBuilds else {
            return
        }
        
        loadingBuilds = true
        defer { loadingBuilds = false }
        
        do {
            builds = try await apiClient.listBuilds(projectId: projectId)
        } catch let appError as AppError {
            if let apiError = appError.type as? APIError {
                switch apiError {
                case .clientRequestError:
                    errorLoadingBuilds = AppError(type: LoadBuildsError.invalidProjectId(projectId: projectId))
                default:
                    ()
                }
            }
            errorLoadingBuilds = appError
        } catch {
            errorLoadingBuilds = AppError(type: LoadBuildsError.unexpected)
        }
    }
}
