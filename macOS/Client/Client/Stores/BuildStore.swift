//
//  BuildStore.swift
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

enum ListAvailableTestsError: LocalizedError {
    case unexpected
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to list the available tests."
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return "Make sure the build is okay and the device is fully ready."
        }
    }
}

class BuildStore: ProjectContext {
    @Published var builds: [Components.Schemas.BuildPublic] = []
    
    @Published var loadingBuilds = false
    @Published var errorLoadingBuilds: AppError?
    
    @Published var addingBuild = false
    @Published var errorAddingBuild: AppError?
    
    @Published var startingBuilds: [String:Bool] = [:]
    @Published var errorStartingBuilds: [String:AppError] = [:]
    
    @Published var streamingBuildsUpdates: [String:Bool] = [:]
    @Published var errorStreamingBuildsUpdates: [String:AppError] = [:]
    
    @Published var buildsListingAvailableTests: [String:Bool] = [:]
    @Published var errorsListingAvailableTests: [String:AppError] = [:]
    
    var uniqueXcTestPlans: [String] {
        Array(Set(builds.map { $0.testPlan }))
    }
    
    func loadBuilds() async {
        guard !loadingBuilds else {
            return
        }
        
        loadingBuilds = true
        defer { loadingBuilds = false }
        
        do {
            let builds = try await apiClient.listBuilds(projectId: projectId)
            for build in builds {
                setBuild(build: build)
            }
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
    
    func addBuild(data: Components.Schemas.StartBuildRequest) async {
        guard !addingBuild else {
            return
        }
        
        addingBuild = true
        defer { addingBuild = false}
        
        do {
            let build = try await BuildStore.startBuild(
                projectId: projectId,
                data: data,
                apiClient: apiClient
            )
            setBuild(build: build)
        } catch {
            errorAddingBuild = (error as! AppError)
        }
    }
    
    func streamUpdates(buildId: String) async {
        guard !(streamingBuildsUpdates[buildId] ?? false) else {
            return
        }
        
        streamingBuildsUpdates[buildId] = true
        defer { streamingBuildsUpdates[buildId] = false }
        
        do {
            let stream = try await apiClient.streamBuildUpdates(projectId: projectId, buildId: buildId)
            for try await newBuild in stream {
                setBuild(build: newBuild)
            }
        } catch let appError as AppError {
            if let apiError = appError.type as? APIError {
                switch apiError {
                case .clientRequestError:
                    errorStreamingBuildsUpdates[buildId] = AppError(type: StreamBuildUpdatesError.invalidProjectId(projectId: projectId))
                default:
                    ()
                }
            }
            errorStreamingBuildsUpdates[buildId] = appError
        } catch {
            errorStreamingBuildsUpdates[buildId] = AppError(type: StreamBuildUpdatesError.unexpected)
        }
    }
    
    func startBuild(buildId: String) async {
        guard !(startingBuilds[buildId] ?? false) else {
            return
        }
        
        startingBuilds[buildId] = true
        defer { startingBuilds[buildId] = false }
        
        do {
            let build = builds.first {$0.id == buildId }!
            let requestData = Components.Schemas.StartBuildRequest(configuration: build.configuration, deviceId: build.deviceId, scheme: build.scheme, testPlan: build.testPlan)
            let newBuild = try await BuildStore.startBuild(projectId: projectId, data: requestData, apiClient: apiClient)
            setBuild(build: newBuild)
        } catch {
            guard error is AppError else {
                fatalError("Expected AppError")
            }
            errorStartingBuilds[buildId] = AppError(type: StartBuildError.unexpected)
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
    
    func loadAvailableTests(buildId: String) async {
        guard !isListingAvailableTests(buildId) else {
            return
        }
        
        buildsListingAvailableTests[buildId] = true
        defer { buildsListingAvailableTests[buildId] = false }
        
        do {
            let xcTestCases = try await apiClient.listAvailableTests(projectId: projectId, buildId: buildId)
            let indexOfBuild = builds.firstIndex(where: { $0.id == buildId })
            builds[indexOfBuild!].xcTestCases = xcTestCases
        } catch let appError as AppError {
            if let apiError = appError.type as? APIError {
                switch apiError {
                case .clientRequestError:
                    errorsListingAvailableTests[buildId] = AppError(type: ListAvailableTestsError.unexpected)
                default:
                    ()
                }
            }
            errorsListingAvailableTests[buildId] = appError
        } catch {
            errorsListingAvailableTests[buildId] =  AppError(type: ListAvailableTestsError.unexpected)
        }
    }
    
    func getBuildById(buildId: String) -> Components.Schemas.BuildPublic? {
        return builds.first { $0.id == buildId }
    }
    
    func setBuild(build: Components.Schemas.BuildPublic) {
        if let existingBuildIndex = builds.firstIndex(where: { $0.id == build.id }) {
            builds[existingBuildIndex] = build
        } else {
            builds.append(build)
        }
    }
    
    func isListingAvailableTests(_ buildId: String) -> Bool {
        return buildsListingAvailableTests[buildId] ?? false
    }
    
    func errorListingAvailableTests(_ buildId: String) -> AppError? {
        return errorsListingAvailableTests[buildId]
    }
}
