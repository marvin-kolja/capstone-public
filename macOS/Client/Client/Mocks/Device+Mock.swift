//
//  Device+Mock.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

extension Components.Schemas.IDeviceStatus {
    static let mock = Components.Schemas.IDeviceStatus(
        ddiMounted: true, developerModeEnabled: true, paired: true, tunnelConnected: true)
}

extension Components.Schemas.DeviceWithStatus {
    static let mock = Components.Schemas.DeviceWithStatus(
        buildVersion: "21F90",
        connected: true,
        deviceClass: "iPhone",
        deviceName: "iPhone",
        id: "00000000-0000000000000000",
        productType: "iPhone12,8",
        productVersion: "17.5.1",
        status: Components.Schemas.IDeviceStatus.mock,
        udid: "00000000-0000000000000000"
    )
}
