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

    var isDeviceReadyForTestSession: Bool {
        guard isDeviceReadyForBuilds else {
            return false
        }

        guard let status = status else {
            return false
        }

        // If tunnel connected is nil it indicates that the device does not need it.
        guard status.tunnelConnected == nil || status.tunnelConnected == true else {
            return false
        }

        return true
    }

    var isDeviceReadyForBuilds: Bool {
        guard isConnected else {
            return false
        }

        guard let status = status else {
            return false
        }

        guard status.paired else {
            return false
        }

        // If developer mode is nil it indicates that the device does not need it.
        guard status.developerModeEnabled == nil || status.developerModeEnabled == true else {
            return false
        }

        guard status.ddiMounted else {
            return false
        }

        return true
    }
}
