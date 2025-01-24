//
//  ProjectsStore.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import Foundation

enum LoadProjectsError: LocalizedError {
    case unexpected
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "An unexpected error occured while loading the projects"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        }
    }
}

enum AddProjectError: LocalizedError {
    case unexpected
    case invalidPath(url: URL, reason: String?)
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to add the project."
        case .invalidPath(_, let reason):
            guard let reason = reason else {
                return "The given path is invalid."
            }
            return "Unable to add project because: '\(reason)'"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidPath(_, _):
            return "Make sure the path points to a valid xcode project."
        }
    }
}

@MainActor
class ProjectsStore: APIClientContext {
    @Published var projects: [Components.Schemas.XcProjectPublic] = []
    
    @Published var errorLoadingProjects: AppError?
    @Published var loadingProjects = false
    
    @Published var errorAddingProject: AppError?
    @Published var showAddingProjectError = false
    @Published var addingProject = false
    
    override init(apiClient: APIClientProtocol) {
        super.init(apiClient: apiClient)
    }
    
    
    func loadProjects() async {
        guard !loadingProjects else {
            return
        }
        
        loadingProjects = true
        defer { loadingProjects = false }
        
        do {
            let newProjects = try await apiClient.listProjects()
            projects = newProjects
        } catch let appError as AppError {
            errorLoadingProjects = appError
        } catch {
            errorLoadingProjects = AppError(type: LoadProjectsError.unexpected)
        }
    }
    
    func addProject(url: URL) async {
        guard !addingProject else {
            return
        }
        
        addingProject = true
        errorAddingProject = nil
        showAddingProjectError = false
        defer {
            addingProject = false
            if errorAddingProject != nil {
                showAddingProjectError = true
            }
        }
        
        do {
            let newProject = try await apiClient.addProject(data: .init(path: "/Users/marvinwillms/GITHUB_PKG_TOKEN.txt"))
            projects.insert(newProject, at: 0)
        } catch let appError as AppError {
            if let apiError = appError.type as? APIError {
                switch apiError {
                case .clientRequestError(_, let detail):
                    errorAddingProject = AppError(type: AddProjectError.invalidPath(url: url, reason: detail))
                default:
                    ()
                }
            }
            errorAddingProject = appError
        } catch {
            errorAddingProject = AppError(type: AddProjectError.unexpected)
        }
    }
}
