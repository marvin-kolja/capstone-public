//
//  Session+Mock.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

import Foundation

extension Components.Schemas.ExecutionStepPublic {
    static let mock: Components.Schemas.ExecutionStepPublic = .init(
        createdAt: .now, endOnFailure: false, id: UUID().uuidString,
        metrics: [Components.Schemas.Metric.cpu], planRepetition: 1, planStepOrder: 0,
        recordingStartStrategy: .launch, reinstallApp: false, stepRepetition: 1,
        testCases: Components.Schemas.BuildPublic.mock.xcTestCases ?? [], testTargetName: "RPSwift",
        updatedAt: .now)

    static var mockMultiple: [Components.Schemas.ExecutionStepPublic] {
        var steps: [Components.Schemas.ExecutionStepPublic] = []

        for i in 1...2 {
            for j in 1...2 {
                for x in 0...2 {
                    for testCase in ["TestCase1", "TestCase2"] {
                        steps.append(
                            .init(
                                createdAt: .now, endOnFailure: false, id: UUID().uuidString,
                                metrics: [Components.Schemas.Metric.cpu], planRepetition: i,
                                planStepOrder: x,
                                recordingStartStrategy: .launch, reinstallApp: false,
                                status: .running,
                                stepRepetition: j, testCases: [testCase], testTargetName: "RPSwift",
                                updatedAt: .now
                            ))
                    }
                }
            }
        }

        return steps
    }
}

extension Components.Schemas.TestSessionPublic {
    static let mock: Components.Schemas.TestSessionPublic = .init(
        buildSnapshot: Components.Schemas.BuildPublic.mock, createdAt: .now,
        deviceSnapshot: Components.Schemas.DeviceWithStatus.mock,
        executionSteps: Components.Schemas.ExecutionStepPublic.mockMultiple, id: UUID().uuidString,
        planSnapshot: Components.Schemas.SessionTestPlanPublic.mock, updatedAt: .now,
        xcTestConfigurationName: "TODO: Xctestrun mock")
}
