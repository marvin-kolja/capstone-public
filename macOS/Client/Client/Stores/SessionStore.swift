//
//  SessionStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

enum LoadSessionsError: LocalizedError {
    case unexpected
    case invalidProjectId

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to load the test sessions."
        case .invalidProjectId:
            return "The given project ID is invalid."
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidProjectId:
            return "Make sure the project still exists."
        }
    }
}

enum StartSessionError: LocalizedError {
    case unexpected
    case invalidTestPlanId(testPlanId: String)

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to start a test session."
        case .invalidTestPlanId:
            return "The given test plan ID is invalid."
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidTestPlanId:
            return "Make sure the test plan exists."
        }
    }
}

enum CancelSessionError: LocalizedError {
    case unexpected

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to cancel the test session."
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return "Ensure the session is valid and active."
        }
    }
}

enum StreamExecutionStepsError: LocalizedError {
    case unexpected

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to stream execution step updates"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return "Make sure the test session is running"
        }
    }
}

enum ExportSessionsError: LocalizedError {
    case unexpected

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to export test session data."
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return "Make sure the trace data still exists"
        }
    }
}

@MainActor
class SessionStore: ProjectContext {
    @Published var sessions: [Components.Schemas.TestSessionPublic] = []

    @Published var loadingSessions = false
    @Published var errorLoadingSessions: AppError?

    @Published var startingSession = false
    @Published var errorStartingSession: AppError?

    @Published var cancelingSessions: [String: Bool] = [:]
    @Published var errorCancelingSessions: [String: AppError] = [:]

    @Published var streamingSessionUpdates: [String: Bool] = [:]
    @Published var errorStreamingSessionUpdates: [String: AppError] = [:]
    
    @Published var exportingSessionResults: [String: Bool] = [:]
    @Published var errorExportingSessionResults: [String: AppError] = [:]

    func loadSessions() async {
        guard !loadingSessions else { return }

        loadingSessions = true
        defer { loadingSessions = false }

        do {
            let sessions = try await apiClient.listTestSession(projectId: projectId)
            self.sessions = sessions
        } catch let appError as AppError {
            errorLoadingSessions = appError
        } catch {
            errorLoadingSessions = AppError(type: LoadSessionsError.unexpected)
        }
    }

    func startSession(data: Components.Schemas.TestSessionCreate) async {
        guard !startingSession else { return }

        startingSession = true
        defer { startingSession = false }

        do {
            let session = try await apiClient.startTestSession(data: data)
            sessions.append(session)
        } catch let appError as AppError {
            errorStartingSession = appError
        } catch {
            errorStartingSession = AppError(type: StartSessionError.unexpected)
        }
    }

    func cancelSession(sessionId: String) async {
        guard !(cancelingSessions[sessionId] ?? false) else { return }

        cancelingSessions[sessionId] = true
        defer { cancelingSessions[sessionId] = false }

        do {
            try await apiClient.cancelTestSession(sessionId: sessionId)
        } catch let appError as AppError {
            errorCancelingSessions[sessionId] = appError
        } catch {
            errorCancelingSessions[sessionId] = AppError(type: CancelSessionError.unexpected)
        }
    }

    func streamSessionUpdates(sessionId: String) async {
        guard !(streamingSessionUpdates[sessionId] ?? false) else { return }

        streamingSessionUpdates[sessionId] = true
        defer {
            streamingSessionUpdates[sessionId] = false
            
            Task {
                // TODO: Just reload the specific session
                await loadSessions()
            }
        }

        do {
            let stream = try await apiClient.streamSessionExecutionStepUpdates(sessionId: sessionId)
            for try await update in stream {
                replaceExecutionStep(sessionId: sessionId, executionStep: update)
            }
        } catch let appError as AppError {
            errorStreamingSessionUpdates[sessionId] = appError
        } catch {
            errorStreamingSessionUpdates[sessionId] = AppError(type: StreamExecutionStepsError.unexpected)
        }
    }

    func exportSessionResults(sessionId: String) async {
        guard !(exportingSessionResults[sessionId] ?? false) else { return }

        exportingSessionResults[sessionId] = true
        defer { exportingSessionResults[sessionId] = false }
        
        do {
            try await apiClient.exportSessionResults(sessionId: sessionId)
        } catch let appError as AppError {
            errorExportingSessionResults[sessionId] = appError
        } catch {
            errorExportingSessionResults[sessionId] = AppError(type: ExportSessionsError.unexpected)
        }
    }

    private func replaceExecutionStep(sessionId: String, executionStep: Components.Schemas.ExecutionStepPublic) {
        if let sessionIndex = getSessionIndex(sessionId) {
            if let stepIndex = sessions[sessionIndex].executionSteps.firstIndex(where: { $0.id == executionStep.id }) {
                sessions[sessionIndex].executionSteps[stepIndex] = executionStep
            }
        }
    }

    func getSessionIndex(_ sessionId: String) -> Int? {
        return sessions.firstIndex(where: { $0.id == sessionId })
    }

    func getSessionById(_ sessionId: String) -> Components.Schemas.TestSessionPublic? {
        return sessions.first(where: { $0.id == sessionId })
    }
}

