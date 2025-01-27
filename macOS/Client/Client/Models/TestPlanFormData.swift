//
//  TestPlanFormData.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

struct TestPlanFormData {
    let id: String
    
    var name: String = ""
    var xcTestPlanName: String = ""
    let defaultXcTestPlanName: String?
    var endOnFailure: Bool = false
    var reinstallApp: Bool = false
    var repetitions: Int = 1
    var recordingStartStrategy: Components.Schemas.RecordingStartStrategy = .launch
    var recordingStrategy: Components.Schemas.RecordingStrategy = .perStep
    var repetitionStrategy: Components.Schemas.RepetitionStrategy = .entireSuite
    var metrics: [Components.Schemas.Metric] = []

    /// Uses the test plan data to create form data
    static func fromExisting(testPlan: Components.Schemas.SessionTestPlanPublic) -> TestPlanFormData {
        return .init(
            id: testPlan.id,
            name: testPlan.name,
            xcTestPlanName: testPlan.xcTestPlanName,
            defaultXcTestPlanName: testPlan.xcTestPlanName,
            endOnFailure: testPlan.endOnFailure,
            reinstallApp: testPlan.reinstallApp,
            repetitions: testPlan.repetitions,
            recordingStartStrategy: testPlan.recordingStartStrategy,
            recordingStrategy: testPlan.recordingStrategy,
            repetitionStrategy: testPlan.repetitionStrategy,
            metrics: testPlan.metrics
        )
    }

    /// Creates a create test plan request data from the form data
    func toTestPlanCreate(projectId: String) -> Components.Schemas.SessionTestPlanCreate {
        return .init(
            endOnFailure: endOnFailure,
            metrics: metrics,
            name: name,
            projectId: projectId,
            recordingStartStrategy: recordingStartStrategy,
            recordingStrategy: recordingStrategy,
            reinstallApp: reinstallApp,
            repetitionStrategy: repetitionStrategy,
            repetitions: repetitions,
            xcTestPlanName: xcTestPlanName
        )
    }

    /// Creates a update test plan request data from the form data
    func toTestPlanUpdate() -> Components.Schemas.SessionTestPlanUpdate {
        return .init(
            endOnFailure: endOnFailure,
            metrics: metrics,
            name: name,
            recordingStartStrategy: recordingStartStrategy,
            recordingStrategy: recordingStrategy,
            reinstallApp: reinstallApp,
            repetitionStrategy: repetitionStrategy,
            repetitions: repetitions,
            xcTestPlanName: xcTestPlanName
        )
    }

    func validate() -> Bool {
        guard name != "" && xcTestPlanName != "" else {
            return false
        }
        return true
    }
}
