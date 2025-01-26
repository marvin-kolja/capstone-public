//
//  BuildPublic.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

extension Components.Schemas.BuildPublic {
    var userFriendlyName: String {
        return "\(self.configuration) - \(self.scheme) - \(self.testPlan) - \(self.deviceId)"
    }
}
