//
//  APIClient+Protocol.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

protocol APIClientProtocol {
    func healthCheck() async throws -> Components.Schemas.HealthCheck
    func listProjects() async throws -> [Components.Schemas.XcProjectPublic]
    func addProject(data: Components.Schemas.XcProjectCreate) async throws -> Components.Schemas.XcProjectPublic
}
