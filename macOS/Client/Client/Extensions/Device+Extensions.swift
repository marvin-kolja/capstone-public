//
//  Device+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

extension Components.Schemas.DeviceWithStatus {
    var isConnected: Bool {
        self.connected ?? false
    }
}
