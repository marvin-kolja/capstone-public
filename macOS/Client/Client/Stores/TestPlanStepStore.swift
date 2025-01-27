//
//  TestPlanStore.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import Foundation

enum AddTestPlanStepError: LocalizedError {
    case unexpected
    case invalidRequestData

    var failureReason: String? {
        switch self {
        case .unexpected, .invalidRequestData:
            return "We were unable to add the test plan step"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected, .invalidRequestData:
            return nil
        }
    }
}

enum UpdateTestPlanStepError: LocalizedError {
    case unexpected
    case invalidRequestData

    var failureReason: String? {
        switch self {
        case .unexpected, .invalidRequestData:
            return "We were unable to update the test plan step"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected, .invalidRequestData:
            return nil
        }
    }
}

enum DeleteTestPlanStepError: LocalizedError {
    case unexpected

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to delete the test plan step"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        }
    }
}

class TestPlanStepStore: ProjectContext {
    @Published var steps: [Components.Schemas.SessionTestPlanStepPublic]

    @Published var updatingSteps: [String:Bool] = [:]
    @Published var errorUpdatingSteps: [String:AppError] = [:]
    
    @Published var addingStep = false
    @Published var errorAddingStep: AppError?
    
    @Published var deletingSteps: [String:Bool] = [:]
    @Published var errorDeletingSteps: [String:AppError] = [:]

    private let testPlanId: String

    init(projectId: String, testPlanId: String, apiClient: APIClientProtocol, steps: [Components.Schemas.SessionTestPlanStepPublic]) {
        _steps = Published(initialValue: steps)
        self.testPlanId = testPlanId
        super.init(projectId: projectId, apiClient: apiClient)
    }
    
    func add(data: Components.Schemas.SessionTestPlanStepCreate) async {
        guard !addingStep else {
            return
        }

        addingStep = true
        defer { addingStep = false }

        do {
            let step = try await apiClient.createTestPlanStep(testPlanId: testPlanId, data: data)
            setStep(data: step)
        } catch let appError as AppError {
            errorAddingStep = appError
        } catch {
            errorAddingStep = AppError(type: AddTestPlanStepError.unexpected)
        }
    }

    func update(stepId: String, data: Components.Schemas.SessionTestPlanStepUpdate) async {
        guard !(updatingSteps[stepId] ?? false) else {
            return
        }

        updatingSteps[stepId] = true
        defer { updatingSteps[stepId] = false }

        do {
            let step = try await apiClient.updateTestPlanStep(testPlanId: testPlanId, stepId: stepId, data: data)
            setStep(data: step)
        } catch let appError as AppError {
            errorUpdatingSteps[stepId] = appError
        } catch {
            errorUpdatingSteps[stepId] = AppError(type: UpdateTestPlanStepError.unexpected)
        }
    }
    
    
    func delete(stepId: String) async {
        guard !(deletingSteps[stepId] ?? false) else {
            return
        }

        deletingSteps[stepId] = true
        defer { deletingSteps[stepId] = false }

        do {
            try await apiClient.deleteTestPlanStep(testPlanId: testPlanId, stepId: stepId)
            steps.removeAll(where: { $0.id == stepId })
        } catch let appError as AppError {
            errorDeletingSteps[stepId] = appError
        } catch {
            errorDeletingSteps[stepId] = AppError(type: DeleteTestPlanStepError.unexpected)
        }
    }
    
    func getStepById(stepId: String) -> Components.Schemas.SessionTestPlanStepPublic? {
        return steps.first { $0.id == stepId }
    }
    
    func setStep(data: Components.Schemas.SessionTestPlanStepPublic) {
        if let existingBuildIndex = steps.firstIndex(where: { $0.id == data.id }) {
            steps[existingBuildIndex] = data
        } else {
            steps.append(data)
        }
    }
}
