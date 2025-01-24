//
//  Build+Mock.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

extension Components.Schemas.BuildPublic {
    static let mock: Components.Schemas.BuildPublic = .init(
        configuration: Components.Schemas.XcProjectPublic.mock.configurations[0].name,
        deviceId: "Replace When Device mock added",
        id: UUID().uuidString,
        projectId: Components.Schemas.XcProjectPublic.mock.id,
        scheme: Components.Schemas.XcProjectPublic.mock.schemes[0].name,
        testPlan: Components.Schemas.XcProjectPublic.mock.schemes[0].xcTestPlans[0].name
    )
}
