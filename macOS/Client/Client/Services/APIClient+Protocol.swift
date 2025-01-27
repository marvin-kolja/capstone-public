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
    
    func listBuilds(projectId: String) async throws -> [Components.Schemas.BuildPublic]
    func startBuild(projectId: String, data: Components.Schemas.StartBuildRequest) async throws -> Components.Schemas.BuildPublic
    func streamBuildUpdates(projectId: String, buildId: String) async throws -> AsyncThrowingStream<Components.Schemas.BuildPublic, Error>
    
    func listDevices() async throws -> [Components.Schemas.DeviceWithStatus]
    
    func listTestPlans() async throws -> [Components.Schemas.SessionTestPlanPublic]
    func createTestPlan(data: Components.Schemas.SessionTestPlanCreate) async throws -> Components.Schemas.SessionTestPlanPublic
    func updateTestPlan(testPlanId: String, data: Components.Schemas.SessionTestPlanUpdate) async throws -> Components.Schemas.SessionTestPlanPublic
    func deleteTestPlan(testPlanId: String) async throws -> Void
    func createTestPlanStep(testPlanId: String, data: Components.Schemas.SessionTestPlanStepCreate) async throws -> Components.Schemas.SessionTestPlanStepPublic
    func updateTestPlanStep(testPlanId: String, stepId: String, data: Components.Schemas.SessionTestPlanStepUpdate) async throws -> Components.Schemas.SessionTestPlanStepPublic
    func deleteTestPlanStep(testPlanId: String, stepId: String) async throws -> Void
    func reorderTestPlanSteps(testPlanId: String, ids: [String]) async throws
}
