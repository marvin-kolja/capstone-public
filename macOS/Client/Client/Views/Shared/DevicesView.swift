//
//  DevicesView.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

import SwiftUI

struct DevicesView: View {
    @EnvironmentObject var deviceStore: DeviceStore

    @State var selectedDeviceId: String?

    var body: some View {

        VStack(alignment: .center) {
            HStack {
                LoadingButton(
                    isLoading: deviceStore.loadingDevices,
                    action: {
                        Task { await deviceStore.loadDevices() }
                    }
                ) {
                    Image(systemName: "arrow.clockwise")
                }
                Picker("Device", selection: $selectedDeviceId) {
                    ForEach(deviceStore.devices, id: \.id) { device in
                        Text(device.deviceName)
                            .tag(device.id)
                    }
                    Divider().tag(String?(nil))
                }
            }

            Divider()

            if let deviceId = selectedDeviceId,
                let device = deviceStore.getDeviceById(deviceId: deviceId)
            {

                Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
                    GridRow {
                        Text("Name")
                            .bold()
                        Text(device.deviceName)
                    }
                    GridRow {
                        Text("Model")
                            .bold()
                        Text(deviceModels[device.productType] ?? device.productType)
                    }
                    GridRow {
                        Text("Version")
                            .bold()
                        Text("\(device.productVersion) (\(device.buildVersion))")
                    }
                    GridRow {
                        Text("Identifier")
                            .bold()
                        Text(device.udid)
                    }
                    Divider()
                    GridRow {
                        Text("Connected")
                            .bold()
                        Text(device.connected ?? false ? "Yes" : "No")
                    }
                    GridRow {
                        Text("Paired")
                            .bold()
                        Text(device.status?.paired ?? false ? "Yes" : "No")

                        LoadingButton(isLoading: deviceStore.isPairing(deviceId)) {
                            Task {
                                await deviceStore.pair(deviceId)
                                await deviceStore.loadDevices()
                            }
                        } label: {
                            Text("Pair")
                        }
                        .disabled(device.status?.paired ?? true)

                    }.disabled(!device.isConnected)
                    GridRow {
                        Text("Developer Mode Enabled")
                            .bold()
                        Text(device.status?.developerModeEnabled ?? false ? "Yes" : "No")

                        LoadingButton(isLoading: deviceStore.isEnablingDeveloperMode(deviceId)) {
                            Task {
                                await deviceStore.enableDeveloperMode(deviceId)
                                await deviceStore.loadDevices()
                            }
                        } label: {
                            Text("Enable")
                        }
                        .disabled(device.status?.developerModeEnabled ?? true)
                    }.disabled(!device.isConnected || device.status?.developerModeEnabled == nil)
                    GridRow {
                        Text("DDI Mounted")
                            .bold()
                        Text(device.status?.ddiMounted ?? false ? "Yes" : "No")

                        LoadingButton(isLoading: deviceStore.isMounting(deviceId)) {
                            Task {
                                await deviceStore.mountDdi(deviceId)
                                await deviceStore.loadDevices()
                            }
                        } label: {
                            Text("Enable")
                        }

                        .disabled(device.status?.ddiMounted ?? true)
                    }.disabled(!device.isConnected)
                    GridRow {
                        Text("Tunnel Connected")
                            .bold()
                        Text(device.status?.tunnelConnected ?? false ? "Yes" : "No")

                        LoadingButton(isLoading: deviceStore.isConnectingTunnel(deviceId)) {
                            Task {
                                await deviceStore.connectTunnel(deviceId)
                                await deviceStore.loadDevices()
                            }
                        } label: {
                            Text("Connect")
                        }
                        .disabled(device.status?.tunnelConnected ?? true)
                    }.disabled(!device.isConnected || device.status?.tunnelConnected == nil)
                }
            }
            Spacer()

        }
        .task { await deviceStore.loadDevices() }
        .onChange(of: deviceStore.devices) { oldData, newData in
            if selectedDeviceId == nil {
                selectedDeviceId = newData.first?.id
            }
        }
        .padding()
    }
}

#Preview {
    DevicesView()
        .environmentObject(DeviceStore(apiClient: MockAPIClient()))
}
