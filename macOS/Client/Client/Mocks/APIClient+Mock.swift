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
    
    func listDevices() async throws -> [Components.Schemas.DeviceWithStatus] {
        try? await simulateWork()
        return [Components.Schemas.DeviceWithStatus.mock]
    }
}
