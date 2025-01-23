//
//  APIClient+Protocol.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

protocol APIClientProtocol {
    func checkConnection() async -> Bool
    func listProjects() async throws -> [Components.Schemas.XcProjectPublic]
    func addProject(data: Components.Schemas.XcProjectCreate) async throws -> Components.Schemas.XcProjectPublic
}
