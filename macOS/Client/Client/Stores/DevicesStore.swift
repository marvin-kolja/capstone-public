//
//  DevicesStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

class DevicesStore: APIClientContext {
    @Published var devices: [Components.Schemas.DeviceWithStatus] = []
    
    // TODO: Add methods to manipulate data
}
