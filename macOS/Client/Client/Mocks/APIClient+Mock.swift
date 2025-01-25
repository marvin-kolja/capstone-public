//
//  APIClient+Mock.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import Foundation

class MockAPIClient: APIClientProtocol {
    private func simulateWork() async throws {
        try await Task.sleep(nanoseconds: 1 * NSEC_PER_SEC)
    }
    
    func healthCheck() async throws -> Components.Schemas.HealthCheck {
        try? await simulateWork()
        return Components.Schemas.HealthCheck.mock
    }
    
    func listProjects() async throws -> [Components.Schemas.XcProjectPublic] {
        try? await simulateWork()
        return [Components.Schemas.XcProjectPublic.mock]
    }
    
    func addProject(data: Components.Schemas.XcProjectCreate) async throws -> Components.Schemas.XcProjectPublic {
        try? await simulateWork()
        return Components.Schemas.XcProjectPublic.mock
    }
    
    func listBuilds(projectId: String) async throws -> [Components.Schemas.BuildPublic] {
        try? await simulateWork()
        return [Components.Schemas.BuildPublic.mock]
    }
    
    func startBuild(projectId: String, data: Components.Schemas.StartBuildRequest) async throws -> Components.Schemas.BuildPublic {
        try? await simulateWork()
        var build_not_running = Components.Schemas.BuildPublic.mock
        build_not_running.status = .pending
        return build_not_running
    }
    
    func streamBuildUpdates(projectId: String, buildId: String) async throws -> AsyncThrowingStream<Components.Schemas.BuildPublic, any Error> {
        try? await simulateWork()
        return AsyncThrowingStream { continuation in
            Task {
                try? await simulateWork()
                
                var build_running = Components.Schemas.BuildPublic.mock
                build_running.status = .running
                continuation.yield(build_running)
                
                try? await simulateWork()
                
                var build_success = Components.Schemas.BuildPublic.mock
                build_success.status = .success
                // TODO: add xctestrun data
                continuation.yield(build_success)
                
                continuation.finish()
            }
        }
    }
    
    func listDevices() async throws -> [Components.Schemas.DeviceWithStatus] {
        try? await simulateWork()
        return [Components.Schemas.DeviceWithStatus.mock]
    }
}
