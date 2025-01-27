//
//  Build+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

extension Components.Schemas.BuildPublic {
    var isBuildReadyForTests: Bool {
        guard status == .success else {
            return false
        }
        
        guard let _xctestrun = xctestrun else {
            return false
        }
        
        guard let _xcTestCases = xcTestCases, !_xcTestCases.isEmpty else {
            return false
        }
        
        return true
    }
}
