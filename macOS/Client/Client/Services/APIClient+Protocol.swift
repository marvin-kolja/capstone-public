//
//  APIClient+Protocol.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

protocol APIClientProtocol {
    func healthCheck() async throws -> Components.Schemas.HealthCheck
    func listProjects() async throws -> [Components.Schemas.XcProjectPublic]
    func addProject(data: Components.Schemas.XcProjectCreate) async throws
        -> Components.Schemas.XcProjectPublic

    func listBuilds(projectId: String) async throws -> [Components.Schemas.BuildPublic]
    func startBuild(projectId: String, data: Components.Schemas.StartBuildRequest) async throws
        -> Components.Schemas.BuildPublic
    func streamBuildUpdates(projectId: String, buildId: String) async throws -> AsyncThrowingStream<
        Components.Schemas.BuildPublic, Error
    >
    func listAvailableTests(projectId: String, buildId: String) async throws -> [String]

    func listDevices() async throws -> [Components.Schemas.DeviceWithStatus]
    func pairDevice(deviceId: String) async throws
    func mountDdi(deviceId: String) async throws
    func enableDeveloperMode(deviceId: String) async throws
    func connectTunnel(deviceId: String) async throws

    func listTestPlans() async throws -> [Components.Schemas.SessionTestPlanPublic]
    func createTestPlan(data: Components.Schemas.SessionTestPlanCreate) async throws
        -> Components.Schemas.SessionTestPlanPublic
    func updateTestPlan(testPlanId: String, data: Components.Schemas.SessionTestPlanUpdate)
        async throws -> Components.Schemas.SessionTestPlanPublic
    func deleteTestPlan(testPlanId: String) async throws
    func createTestPlanStep(testPlanId: String, data: Components.Schemas.SessionTestPlanStepCreate)
        async throws -> Components.Schemas.SessionTestPlanStepPublic
    func updateTestPlanStep(
        testPlanId: String, stepId: String, data: Components.Schemas.SessionTestPlanStepUpdate
    ) async throws -> Components.Schemas.SessionTestPlanStepPublic
    func deleteTestPlanStep(testPlanId: String, stepId: String) async throws
    func reorderTestPlanSteps(testPlanId: String, ids: [String]) async throws

    func listTestSession(projectId: String) async throws -> [Components.Schemas.TestSessionPublic]
    func startTestSession(data: Components.Schemas.TestSessionCreate) async throws
        -> Components.Schemas.TestSessionPublic
    func cancelTestSession(sessionId: String) async throws
    func streamSessionExecutionStepUpdates(sessionId: String) async throws -> AsyncThrowingStream<
        Components.Schemas.ExecutionStepPublic, Error
    >
    func exportSessionResults(sessionId: String) async throws
}
