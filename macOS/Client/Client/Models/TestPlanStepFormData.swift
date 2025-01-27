//
//  TestPlanStepData.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import Foundation

struct TestPlanStepFormData {
    let id: String
    var metrics: [Components.Schemas.Metric]
    var name: String = ""
    var order: Int
    var recordingStartStrategy: Components.Schemas.RecordingStartStrategy
    var reinstallApp: Bool
    var repetitions: Int = 1
    var testCases: [String] = []

    /// Uses the test plan data as default values for new steps
    static func fromTestPlanData(testPlanData: TestPlanFormData, order: Int) -> TestPlanStepFormData {
        return .init(
            id: UUID().uuidString, // Placeholder
            metrics: testPlanData.metrics,
            order: order,
            recordingStartStrategy: testPlanData.recordingStartStrategy,
            reinstallApp: testPlanData.reinstallApp,
            repetitions: 1
        )
    }

    /// Used for steps that already exist. The test plan is used as backup for nil values.
    static func fromExisting(step: Components.Schemas.SessionTestPlanStepPublic, testPlanData: TestPlanFormData) -> TestPlanStepFormData {
        return .init(
            id: step.id,
            metrics: step.metrics ?? testPlanData.metrics,
            name: step.name,
            order: step.order,
            recordingStartStrategy: step.recordingStartStrategy ?? testPlanData.recordingStartStrategy,
            reinstallApp: step.reinstallApp ?? testPlanData.reinstallApp,
            repetitions: step.repetitions ?? 1,
            testCases: step.testCases
        )
    }

    /// Creates a step create request object from the form data
    func toStepCreate() -> Components.Schemas.SessionTestPlanStepCreate {
        return .init(
            metrics: metrics,
            name: name,
            recordingStartStrategy: recordingStartStrategy,
            reinstallApp: reinstallApp,
            repetitions: repetitions,
            testCases: testCases
        )
    }

    /// Creates a step update request object from the form data
    func toStepUpdate() -> Components.Schemas.SessionTestPlanStepUpdate {
        return .init(
            metrics: metrics,
            name: name,
            recordingStartStrategy: recordingStartStrategy,
            reinstallApp: reinstallApp,
            repetitions: repetitions,
            testCases: testCases
        )
    }

    func validate() -> Bool {
        guard name != "" && !testCases.isEmpty else {
            return false
        }
        return true
    }
}
