//
//  AddBuildView.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import SwiftUI

struct AddBuildView: View {
    @Environment(\.dismiss) private var dismiss

    @EnvironmentObject var buildStore: BuildStore
    @EnvironmentObject var deviceStore: DeviceStore
    @EnvironmentObject var currentProjectStore: CurrentProjectStore

    @State var configuration: Components.Schemas.XcProjectConfigurationPublic?
    @State var deviceId: String?
    @State var scheme: Components.Schemas.XcProjectSchemePublic?
    @State var testPlan: Components.Schemas.XcProjectTestPlanPublic?

    var body: some View {
        VStack(spacing: 10) {
            Text("Start a new build")
                .font(.title2)
            Picker("Configuration", selection: $configuration) {
                ForEach(currentProjectStore.project.configurations, id: \.self) { config in
                    Text(config.name)
                        .tag(config)
                }
                Divider().tag(Components.Schemas.XcProjectConfigurationPublic?(nil))
            }
            Picker("Scheme", selection: $scheme) {
                ForEach(currentProjectStore.project.schemes, id: \.self) { scheme in
                    Text(scheme.name)
                        .tag(scheme)
                }
                Divider().tag(Components.Schemas.XcProjectSchemePublic?(nil))
            }
            Picker("Test Plan", selection: $testPlan) {
                ForEach(scheme?.xcTestPlans ?? [], id: \.self) { testPlan in
                    Text(testPlan.name)
                        .tag(testPlan)
                }
                Divider().tag(Components.Schemas.XcProjectTestPlanPublic?(nil))
            }.disabled(scheme == nil)

            HStack {
                LoadingButton(
                    isLoading: deviceStore.loadingDevices,
                    action: {
                        Task { await deviceStore.loadDevices() }
                    }
                ) {
                    Image(systemName: "arrow.clockwise")
                }
                Picker("Devices", selection: $deviceId) {
                    ForEach(deviceStore.devices, id: \.id) { device in
                        Text("\(device.deviceName) (\(device.udid))")
                            .tag(device.id)
                    }
                    Divider().tag(String?(nil))
                }
            }
            if deviceId != nil && !isDeviceConnected {
                Text("Device is not connected")
                    .bold()
                    .foregroundStyle(.orange)
            }

            HStack {
                Button("Cancel") {
                    dismiss()
                }.disabled(buildStore.addingBuild)
                Spacer()
                LoadingButton(
                    isLoading: buildStore.addingBuild,
                    action: {
                        Task {
                            defer { dismiss() }

                            await buildStore.addBuild(
                                data: .init(
                                    configuration: configuration!.name,
                                    deviceId: deviceId!,
                                    scheme: scheme!.name,
                                    testPlan: testPlan!.name
                                )
                            )
                        }
                    }
                ) {
                    Text("Start Build")
                }.disabled(startButtonDisabled)
            }
        }
        .padding(20)
    }

    var startButtonDisabled: Bool {
        return configuration == nil || scheme == nil || testPlan == nil || !isDeviceConnected
    }

    var isDeviceConnected: Bool {
        guard let deviceId = deviceId, let device = deviceStore.getDeviceById(deviceId: deviceId)
        else {
            return false
        }

        return device.connected ?? false
    }
}

#Preview {
    AddBuildView()
        .environmentObject(
            BuildStore(
                projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient())
        )
        .environmentObject(DeviceStore(apiClient: MockAPIClient()))
        .environmentObject(CurrentProjectStore(project: Components.Schemas.XcProjectPublic.mock))
}
