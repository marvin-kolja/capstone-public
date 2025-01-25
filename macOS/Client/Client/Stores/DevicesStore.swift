//
//  DevicesStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

enum LoadDevicesError: LocalizedError {
    case unknown
}

class DevicesStore: APIClientContext {
    @Published var devices: [Components.Schemas.DeviceWithStatus] = []
    @Published var loadingDevices = false
    @Published var loadingDevicesError: AppError?
    
    func loadDevices() async {
        guard !loadingDevices else {
            return
        }
        
        loadingDevices = true
        defer { loadingDevices = false }
        
        do {
            devices = try await apiClient.listDevices()
        } catch let appError as AppError {
            loadingDevicesError = appError
        } catch {
            loadingDevicesError = AppError(type: LoadDevicesError.unknown)
        }
    }
}
