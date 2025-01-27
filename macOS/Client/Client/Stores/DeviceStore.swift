//
//  DeviceStore.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Foundation

enum LoadDevicesError: LocalizedError {
    case unknown
}

enum DeviceActionError: LocalizedError {
    case unknown
}

class DeviceStore: APIClientContext {
    @Published var devices: [Components.Schemas.DeviceWithStatus] = []
    @Published var loadingDevices = false
    @Published var loadingDevicesError: AppError?

    @Published var devicesPairing: [String:Bool] = [:]
    @Published var devicesMounting: [String:Bool] = [:]
    @Published var devicesEnablingDeveloperMode: [String:Bool] = [:]
    @Published var devicesConnectingTunnel: [String:Bool] = [:]

    @Published var devicePairingErros: [String:AppError] = [:]
    @Published var deviceMountingErros: [String:AppError] = [:]
    @Published var deviceEnablingDeveloperModeErros: [String:AppError] = [:]
    @Published var deviceConnectingTunnelErros: [String:AppError] = [:]

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

    func pair(_ deviceId: String) async {
        guard !isPairing(deviceId) else {
            return
        }

        devicesPairing[deviceId] = true
        defer { devicesMounting[deviceId] = false }

        do {
            try await apiClient.pairDevice(deviceId: deviceId)
        } catch let appError as AppError {
            devicePairingErros[deviceId] = appError
        } catch {
            devicePairingErros[deviceId] = AppError(type: DeviceActionError.unknown)
        }
    }

    func mountDdi(_ deviceId: String) async {
        guard !isMounting(deviceId) else {
            return
        }

        devicesMounting[deviceId] = true
        defer { devicesMounting[deviceId] = false }

        do {
            try await apiClient.mountDdi(deviceId: deviceId)
        } catch let appError as AppError {
            deviceMountingErros[deviceId] = appError
        } catch {
            deviceMountingErros[deviceId] = AppError(type: DeviceActionError.unknown)
        }
    }

    func enableDeveloperMode(_ deviceId: String) async {
        guard !isEnablingDeveloperMode(deviceId) else {
            return
        }

        devicesEnablingDeveloperMode[deviceId] = true
        defer { devicesEnablingDeveloperMode[deviceId] = false }

        do {
            try await apiClient.enableDeveloperMode(deviceId: deviceId)
        } catch let appError as AppError {
            deviceEnablingDeveloperModeErros[deviceId] = appError
        } catch {
            deviceEnablingDeveloperModeErros[deviceId] = AppError(type: DeviceActionError.unknown)
        }
    }

    func connectTunnel(_ deviceId: String) async {
        guard !isConnectingTunnel(deviceId) else {
            return
        }

        devicesConnectingTunnel[deviceId] = true
        defer { devicesConnectingTunnel[deviceId] = false }

        do {
            try await apiClient.connectTunnel(deviceId: deviceId)
        } catch let appError as AppError {
            deviceConnectingTunnelErros[deviceId] = appError
        } catch {
            deviceConnectingTunnelErros[deviceId] = AppError(type: DeviceActionError.unknown)
        }
    }

    func getDeviceById(deviceId: String) -> Components.Schemas.DeviceWithStatus? {
        return devices.first(where: { $0.id == deviceId })
    }

    func isPairing(_ deviceId: String) -> Bool {
        return devicesPairing[deviceId] ?? false
    }

    func isMounting(_ deviceId: String) -> Bool {
        return devicesMounting[deviceId] ?? false
    }

    func isEnablingDeveloperMode(_ deviceId: String) -> Bool {
        return devicesEnablingDeveloperMode[deviceId] ?? false
    }

    func isConnectingTunnel(_ deviceId: String) -> Bool {
        return devicesConnectingTunnel[deviceId] ?? false
    }
}
