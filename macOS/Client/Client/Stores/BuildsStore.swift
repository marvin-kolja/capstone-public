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
    @Published var buildStores: [BuildStore] = []
    
    @Published var loadingBuilds = false
    @Published var errorLoadingBuilds: AppError?
    
    func loadBuilds() async {
        guard !loadingBuilds else {
            return
        }
        
        loadingBuilds = true
        defer { loadingBuilds = false }
        
        do {
            let builds = try await apiClient.listBuilds(projectId: projectId)
            createBuildStores(builds: builds)
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
    
    private func createBuildStores(builds: [Components.Schemas.BuildPublic]) {
        for build in builds {
            if let existing = buildStores.first(where: { $0.build.id == build.id }) {
                existing.build = build
            } else {
                buildStores.append(BuildStore(projectId: projectId, apiClient: apiClient, build: build))
            }
        }
    }
}
