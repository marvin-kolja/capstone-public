//
//  TestPlan+Mock.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import Foundation

extension Components.Schemas.SessionTestPlanStepPublic {
    static let mock = Components.Schemas.SessionTestPlanStepPublic(
        id: UUID().uuidString,
        name: "First Step",
        order: 0,
        testCases: [
            "RPSwiftUI/RPSwiftUI/someTestCase"
        ]
    )
}

extension Components.Schemas.SessionTestPlanPublic {
    static let mock = Components.Schemas.SessionTestPlanPublic(
        endOnFailure: true,
        id: UUID().uuidString,
        metrics: [Components.Schemas.Metric.cpu],
        name: "Mock Test Plan",
        projectId: Components.Schemas.XcProjectPublic.mock.id,
        recordingStartStrategy: Components.Schemas.RecordingStartStrategy.launch,
        recordingStrategy: Components.Schemas.RecordingStrategy.perTest,
        reinstallApp: false,
        repetitionStrategy: Components.Schemas.RepetitionStrategy.entireSuite,
        repetitions: 1,
        steps: [Components.Schemas.SessionTestPlanStepPublic.mock],
        xcTestPlanName: Components.Schemas.BuildPublic.mock.testPlan
    )
}
