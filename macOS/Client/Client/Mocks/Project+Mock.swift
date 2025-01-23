//
//  Project+Mock.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

extension Components.Schemas.XcProjectTestPlanPublic {
    static let mock: Components.Schemas.XcProjectTestPlanPublic = .init(name: "Test Plan")
}

extension Components.Schemas.XcProjectSchemePublic {
    static let mock: Components.Schemas.XcProjectSchemePublic = .init(
        name: "Release",
        xcTestPlans: [Components.Schemas.XcProjectTestPlanPublic.mock]
    )
}

extension Components.Schemas.XcProjectTargetPublic {
    static let mock: Components.Schemas.XcProjectTargetPublic = .init(name: "Target")
}

extension Components.Schemas.XcProjectConfigurationPublic {
    static let mock: Components.Schemas.XcProjectConfigurationPublic = .init(name: "Configuration")
}

extension Components.Schemas.XcProjectPublic {
    static let mock: Components.Schemas.XcProjectPublic = .init(
        configurations: [Components.Schemas.XcProjectConfigurationPublic.mock, Components.Schemas.XcProjectConfigurationPublic.mock],
        id: "some_id",
        name: "RP Swift",
        path: "/Path/to/project.xcodeproj",
        schemes: [Components.Schemas.XcProjectSchemePublic.mock, Components.Schemas.XcProjectSchemePublic.mock],
        targets: [Components.Schemas.XcProjectTargetPublic.mock, Components.Schemas.XcProjectTargetPublic.mock]
    )
}
