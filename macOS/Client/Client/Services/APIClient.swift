//
//  APIClient.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import Foundation
import OpenAPIAsyncHTTPClient
import AsyncHTTPClient
import OpenAPIRuntime
import Logging
import Combine

enum APIError: LocalizedError {
    case clientRequestError(statusCode: Int, detail: String? = nil)
    case serverError(statusCode: Int, detail: String? = nil)
    case unknownStatus(statusCode: Int)
    case deadServer
    case timeout
    case unexpected(Error)
    
    var failureReason: String? {
        switch self {
        case .clientRequestError(_, let detail):
            "Request error with because '\(detail ?? "no info")'"
        case .serverError(_, _):
            "A server error occured"
        case .unknownStatus(let statusCode):
            "An unknown non-ok status code was returned '\(statusCode)'"
        case .deadServer:
            "The server is not reachable"
        case .timeout:
            "The connection to the server timed out"
        case .unexpected:
            "An unexpected error occured while making the request"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .clientRequestError(_, _):
            "Try fixing what you're sending to the server"
        case .serverError(_, _):
            "Check the server"
        case .unknownStatus(_):
            "Check the server"
        case .deadServer:
            "Make sure the server is running"
        case .timeout:
            "Make sure the server is running"
        case .unexpected:
            nil
        }
    }
}

class APIClient: APIClientProtocol {
    private let client: Client
    private let httpClient: HTTPClient
    private let serverURL: URL
    
    let apiCallSuccessSubject = PassthroughSubject<Bool,Never>()
    
    private let decoder: JSONDecoder
    
    init() throws {
        let timeout = HTTPClient.Configuration.Timeout(connect: .seconds(1), read: .minutes(1))
        self.httpClient = HTTPClient(eventLoopGroupProvider: .singleton,
                                     configuration: HTTPClient.Configuration(timeout: timeout))
        
        self.serverURL = try Servers.Server2.url()
        self.client = Client(
            serverURL: serverURL,
            configuration: .init(dateTranscoder: .iso8601),
            transport: AsyncHTTPClientTransport(configuration: .init(client: httpClient, timeout: .minutes(1)))
        )
        
        self.decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
    }
    
    /// Generic API request handler that throws an `APIError.unknown` on any unknown errors that happen during
    /// the request or response handling.
    private func handleRequestError<T>(
        _ apiCall: () async throws -> T
    ) async throws -> T {
        do {
            do {
                let data = try await apiCall()
                apiCallSuccessSubject.send(true)
                return data
            } catch let apiError as APIError {
                logger.debug("[API] APIError: \(apiError)")
                throw AppError(type: apiError)
            } catch let clientError as ClientError {
                logger.debug("[API] ClientError: \(clientError)")
                if let posixError = clientError.underlyingError as? HTTPClient.NWPOSIXError {
                    if posixError.errorCode.rawValue == ECONNREFUSED {
                        throw AppError(type: APIError.deadServer)
                    }
                }
                
                if let httpClientError = clientError.underlyingError as? HTTPClientError {
                    switch httpClientError {
                    case .deadlineExceeded, .connectTimeout, .readTimeout, .writeTimeout:
                        throw AppError(type: APIError.timeout)
                    default:
                        ()
                    }
                }
                throw AppError(type: APIError.unexpected(clientError))
            } catch {
                logger.debug("[API] Error: \(error)")
                throw AppError(type: APIError.unexpected(error))
            }
        } catch {
            apiCallSuccessSubject.send(false)
            throw error
        }
    }
    
    func healthCheck() async throws -> Components.Schemas.HealthCheck {
        try await handleRequestError {
            let result = try await client.healthHealthCheck()
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .undocumented(let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func listProjects() async throws -> [Components.Schemas.XcProjectPublic] {
        try await handleRequestError {
            let result = try await client.projectsListProjects()
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func addProject(data: Components.Schemas.XcProjectCreate) async throws -> Components.Schemas.XcProjectPublic {
        try await handleRequestError {
            let result = try await client.projectsAddProject(body: .json(data))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            case .unprocessableContent(let response):
                throw APIError.clientRequestError(statusCode: 422, detail: try response.body.json.detail.description)
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func listBuilds(projectId: String) async throws -> [Components.Schemas.BuildPublic] {
        try await handleRequestError {
            let result = try await client.projectsListBuilds(.init(path: .init(projectId: projectId)))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .unprocessableContent(let response):
                throw APIError.clientRequestError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func startBuild(projectId: String, data: Components.Schemas.StartBuildRequest) async throws -> Components.Schemas.BuildPublic {
        try await handleRequestError {
            let result = try await client.projectsStartBuild(.init(path: .init(projectId: projectId), body: .json(data)))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound(let response):
                throw APIError.clientRequestError(statusCode: 404, detail: try response.body.json.detail)
            case .unprocessableContent(let response):
                throw APIError.clientRequestError(statusCode: 422, detail: try response.body.json.detail.description)
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func streamBuildUpdates(projectId: String, buildId: String) async throws -> AsyncThrowingStream<Components.Schemas.BuildPublic, Error> {
        try await handleRequestError {
            let result = try await client.projectsStreamBuildUpdates(.init(path: .init(projectId: projectId, buildId: buildId)))
            
            switch result {
            case .ok(let okResponse):
                let stream = try okResponse.body.textEventStream.asDecodedServerSentEventsWithJSONData(
                    of: Components.Schemas.BuildPublic.self
                )
                return AsyncThrowingStream { continuation in
                    let task = Task {
                        do {
                            logger.debug("Listening for build updates")
                            for try await build in stream {
                                if let build = build.data {
                                    logger.debug("Got new build: \(build.id)")
                                    continuation.yield(build)
                                } else {
                                    logger.debug("Got nil build")
                                }
                            }
                            logger.debug("Finish listening to build updates")
                            continuation.finish()
                        } catch {
                            logger.warning("Finish listening to build updates with error \(error)")
                        }
                    }
                    
                    continuation.onTermination = { _ in
                        task.cancel()
                    }
                }
                
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound(let response):
                throw APIError.clientRequestError(statusCode: 404, detail: try response.body.json.detail)
            case .unprocessableContent(let response):
                throw APIError.clientRequestError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func listAvailableTests(projectId: String, buildId: String) async throws -> [String] {
        try await handleRequestError {
            let result = try await client.projectsListAvailableTests(.init(path: .init(projectId: projectId, buildId: buildId)))
            switch result {
            case .ok(let response):
                return try response.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            case .notFound(let response):
                throw APIError.clientRequestError(statusCode: 404, detail: try response.body.json.detail)
            case .unprocessableContent(_):
                throw APIError.clientRequestError(statusCode: 422)
            }
        }
    }
    
    func listDevices() async throws -> [Components.Schemas.DeviceWithStatus] {
        try await handleRequestError {
            let result = try await client.devicesListDevices()
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func pairDevice(deviceId: String) async throws -> Void {
        try await handleRequestError {
            let result = try await client.devicesPairDevice(.init(path: .init(deviceId: deviceId)))
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest:
                throw APIError.clientRequestError(statusCode: 400)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(_):
                throw APIError.clientRequestError(statusCode: 422)
            }
        }
    }
    
    func mountDdi(deviceId: String) async throws -> Void {
        try await handleRequestError {
            let result = try await client.devicesMountDdi(.init(path: .init(deviceId: deviceId)))
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest:
                throw APIError.clientRequestError(statusCode: 400)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(_):
                throw APIError.clientRequestError(statusCode: 422)
            }
        }
    }
    
    func enableDeveloperMode(deviceId: String) async throws -> Void {
        try await handleRequestError {
            let result = try await client.devicesEnableDeveloperMode(.init(path: .init(deviceId: deviceId)))
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest:
                throw APIError.clientRequestError(statusCode: 400)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(_):
                throw APIError.clientRequestError(statusCode: 422)
            }
        }
    }
    
    func connectTunnel(deviceId: String) async throws -> Void {
        try await handleRequestError {
            let result = try await client.devicesConnectTunnel(.init(path: .init(deviceId: deviceId)))
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest:
                throw APIError.clientRequestError(statusCode: 400)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(_):
                throw APIError.clientRequestError(statusCode: 422)
            }
        }
    }
    
    func listTestPlans() async throws -> [Components.Schemas.SessionTestPlanPublic] {
        try await handleRequestError {
            let result = try await client.testPlansListTestPlans()
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .unprocessableContent(let response):
                throw APIError.clientRequestError(statusCode: 422)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func createTestPlan(data: Components.Schemas.SessionTestPlanCreate) async throws -> Components.Schemas.SessionTestPlanPublic {
        try await handleRequestError {
            let result = try await client.testPlansCreateTestPlan(body: .json(data))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .badRequest(let response):
                throw APIError.serverError(statusCode: 400, detail: try response.body.json.detail)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func updateTestPlan(testPlanId: String, data: Components.Schemas.SessionTestPlanUpdate) async throws -> Components.Schemas.SessionTestPlanPublic {
        try await handleRequestError {
            let result = try await client.testPlansUpdateTestPlan(path: .init(testPlanId: testPlanId), body: .json(data))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .badRequest(let response):
                throw APIError.serverError(statusCode: 400, detail: try response.body.json.detail)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func deleteTestPlan(testPlanId: String) async throws -> Void {
        try await handleRequestError {
            let result = try await client.testPlansDeleteTestPlan(path: .init(testPlanId: testPlanId))
            
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func createTestPlanStep(testPlanId: String, data: Components.Schemas.SessionTestPlanStepCreate) async throws -> Components.Schemas.SessionTestPlanStepPublic {
        try await handleRequestError {
            let result = try await client.testPlansCreateTestPlanStep(path: .init(testPlanId: testPlanId), body: .json(data))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func updateTestPlanStep(testPlanId: String, stepId: String, data: Components.Schemas.SessionTestPlanStepUpdate) async throws -> Components.Schemas.SessionTestPlanStepPublic {
        try await handleRequestError {
            let result = try await client.testPlansUpdateTestPlanStep(path: .init(testPlanId: testPlanId, stepId: stepId), body: .json(data))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func deleteTestPlanStep(testPlanId: String, stepId: String) async throws -> Void {
        try await handleRequestError {
            let result = try await client.testPlansDeleteTestPlanStep(path: .init(testPlanId: testPlanId, stepId: stepId))
            
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func reorderTestPlanSteps(testPlanId: String, ids: [String]) async throws {
        try await handleRequestError {
            let result = try await client.testPlansReorderTestPlanSteps(path: .init(testPlanId: testPlanId), body: .json(ids))
            
            switch result {
            case .ok(let okResponse):
                return // API returns just a status code and empty JSON
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .notFound:
                throw APIError.clientRequestError(statusCode: 404)
            case .unprocessableContent(let response):
                throw APIError.serverError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func listTestSession(projectId: String) async throws -> [Components.Schemas.TestSessionPublic] {
        try await handleRequestError {
            let result = try await client.testSessionListTestSessions(query: .init(projectId: projectId))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .unprocessableContent:
                throw APIError.clientRequestError(statusCode: 422)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func startTestSession(data: Components.Schemas.TestSessionCreate) async throws -> Components.Schemas.TestSessionPublic {
        try await handleRequestError {
            let result = try await client.testSessionStartTestSession(body: .json(data))
            
            switch result {
            case .ok(let okResponse):
                return try okResponse.body.json
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .unprocessableContent:
                throw APIError.clientRequestError(statusCode: 422)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            }
        }
    }
    
    func cancelTestSession(sessionId: String) async throws {
        try await handleRequestError {
            let result = try await client.testSessionCancelTestSession(path: .init(testSessionId: sessionId))
            
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .unprocessableContent:
                throw APIError.clientRequestError(statusCode: 422)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            case .notFound(let response):
                throw APIError.clientRequestError(statusCode: 404, detail: try response.body.json.detail)
            }
        }
    }
    
    func streamSessionExecutionStepUpdates(sessionId: String) async throws -> AsyncThrowingStream<Components.Schemas.ExecutionStepPublic, any Error> {
        try await handleRequestError {
            let result = try await client.testSessionStreamExecutionStepUpdates(path: .init(testSessionId: sessionId))
            
            switch result {
            case .ok(let okResponse):
                let stream = try okResponse.body.textEventStream.asDecodedServerSentEventsWithJSONData(
                    of: Components.Schemas.ExecutionStepPublic.self,
                    decoder: decoder
                )
                return AsyncThrowingStream { continuation in
                    let task = Task {
                        do {
                            logger.debug("Listening for execution step updates")
                            for try await event in stream {
                                if let stepData = event.data {
                                    logger.debug("Got new execution step: \(stepData.id)")
                                    continuation.yield(stepData)
                                } else {
                                    logger.debug("Got nil execution step")
                                }
                            }
                            logger.debug("Finish listening to execution step updates")
                            continuation.finish()
                        } catch {
                            logger.warning("Finish listening to execution step updates with error \(error)")
                            continuation.finish(throwing: error)
                        }
                    }
                    
                    continuation.onTermination = { _ in
                        task.cancel()
                    }
                }
                
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            case .notFound(let response):
                throw APIError.clientRequestError(statusCode: 404, detail: try response.body.json.detail)
            case .unprocessableContent(let response):
                throw APIError.clientRequestError(statusCode: 422, detail: try response.body.json.detail.description)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            }
        }
    }
    
    func exportSessionResults(sessionId: String) async throws {
        try await handleRequestError {
            let result = try await client.testSessionExportTestSessionResults(path: .init(testSessionId: sessionId))
            
            switch result {
            case .ok:
                return
            case .internalServerError:
                throw APIError.serverError(statusCode: 500)
            case .unprocessableContent:
                throw APIError.clientRequestError(statusCode: 422)
            case .undocumented(statusCode: let statusCode, _):
                throw APIError.unknownStatus(statusCode: statusCode)
            case .badRequest(let response):
                throw APIError.clientRequestError(statusCode: 400, detail: try response.body.json.detail)
            case .notFound(let response):
                throw APIError.clientRequestError(statusCode: 404, detail: try response.body.json.detail)
            }
        }
    }
}
