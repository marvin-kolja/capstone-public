//
//  TestPlanStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

enum LoadTestPlansError: LocalizedError {
    case unexpected

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to load the test plans."
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        }
    }
}

enum AddTestPlanError: LocalizedError {
    case unexpected
    case invalidRequestData

    var failureReason: String? {
        switch self {
        case .unexpected, .invalidRequestData:
            return "We were unable to update the test plan"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidRequestData:
            return "Make sure the data you're sending is correct."
        }
    }
}

enum UpdateTestPlanError: LocalizedError {
    case unexpected
    case invalidTestPlanId(testPlanId: String)
    case invalidRequestData

    var failureReason: String? {
        switch self {
        case .unexpected, .invalidRequestData:
            return "We were unable to update the test plan"
        case .invalidTestPlanId:
            return "The test plan does not exist"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidTestPlanId:
            return nil
        case .invalidRequestData:
            return "Make sure the data you're sending is correct."
        }
    }
}

enum DeleteTestPlanError: LocalizedError {
    case unexpected
    case invalidTestPlanId(testPlanId: String)

    var failureReason: String? {
        switch self {
        case .unexpected:
            return "We were unable to delete the test plan"
        case .invalidTestPlanId:
            return "The test plan does not exist"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unexpected:
            return nil
        case .invalidTestPlanId:
            return nil
        }
    }
}

class TestPlanStore: ProjectContext {
    @Published var testPlans: [Components.Schemas.SessionTestPlanPublic] = []

    @Published var loadingTestPlans = false
    @Published var errorLoadingTestPlans: AppError?

    @Published var addingTestPlan = false
    @Published var errorAddingTestPlan: AppError?

    @Published var updatingTestPlans: [String: Bool] = [:]
    @Published var errorUpdatingTestPlans: [String: AppError] = [:]

    @Published var deletingTestPlans: [String: Bool] = [:]
    @Published var errorDeletingTestPlans: [String: AppError] = [:]

    func loadTestPlans() async {
        guard !loadingTestPlans else {
            return
        }

        loadingTestPlans = true
        errorLoadingTestPlans = nil
        defer { loadingTestPlans = false }

        do {
            let testPlans = try await apiClient.listTestPlans()
            for testPlan in testPlans {
                setTestPlan(plan: testPlan)
            }
        } catch let appError as AppError {
            errorLoadingTestPlans = appError
        } catch {
            errorLoadingTestPlans = AppError(type: LoadBuildsError.unexpected)
        }
    }

    func add(data: Components.Schemas.SessionTestPlanCreate) async {
        guard !addingTestPlan else {
            return
        }

        addingTestPlan = true
        defer { addingTestPlan = false }

        do {
            let newTestPlan = try await apiClient.createTestPlan(data: data)
            setTestPlan(plan: newTestPlan)
        } catch let appError as AppError {
            errorAddingTestPlan = appError
        } catch {
            errorAddingTestPlan = AppError(type: AddTestPlanError.unexpected)
        }
    }

    func update(testPlanId: String, data: Components.Schemas.SessionTestPlanUpdate) async {
        guard !(updatingTestPlans[testPlanId] ?? false) else {
            return
        }

        updatingTestPlans[testPlanId] = true
        defer { updatingTestPlans[testPlanId] = false }

        do {
            let newTestPlan = try await apiClient.updateTestPlan(testPlanId: testPlanId, data: data)
            setTestPlan(plan: newTestPlan)
        } catch let appError as AppError {
            errorUpdatingTestPlans[testPlanId] = appError
        } catch {
            errorUpdatingTestPlans[testPlanId] = AppError(type: UpdateTestPlanError.unexpected)
        }
    }

    func delete(testPlanId: String) async {
        guard !(deletingTestPlans[testPlanId] ?? false) else {
            return
        }

        deletingTestPlans[testPlanId] = true
        defer { deletingTestPlans[testPlanId] = false }

        do {
            try await apiClient.deleteTestPlan(testPlanId: testPlanId)
            testPlans.removeAll(where: { $0.id == testPlanId })
        } catch let appError as AppError {
            errorDeletingTestPlans[testPlanId] = appError
        } catch {
            errorDeletingTestPlans[testPlanId] = AppError(type: UpdateTestPlanError.unexpected)
        }
    }

    func getTestPlanById(testPlanId: String) -> Components.Schemas.SessionTestPlanPublic? {
        return testPlans.first { $0.id == testPlanId }
    }

    func setTestPlan(plan: Components.Schemas.SessionTestPlanPublic) {
        if let index = testPlans.firstIndex(where: { $0.id == plan.id }) {
            testPlans[index] = plan
        } else {
            testPlans.append(plan)
        }
    }
}
