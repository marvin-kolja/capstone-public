//
//  AddBuildView.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import SwiftUI

struct AddBuildView: View {
    @Environment(\.dismiss) private var dismiss
    
    @EnvironmentObject var buildsStore: BuildsStore
    @EnvironmentObject var devicesStore: DevicesStore
    @EnvironmentObject var projectStore: ProjectStore
    
    @State var configuration: Components.Schemas.XcProjectConfigurationPublic?
    @State var device: Components.Schemas.DeviceWithStatus?
    @State var scheme: Components.Schemas.XcProjectSchemePublic?
    @State var testPlan: Components.Schemas.XcProjectTestPlanPublic?
    
    var body: some View {
        VStack(spacing: 10) {
            Text("Start a new build")
                .font(.title2)
            Picker("Configuration", selection: $configuration) {
                ForEach(projectStore.project.configurations, id: \.self) { config in
                    Text(config.name)
                        .tag(config)
                }
                Divider().tag(Components.Schemas.XcProjectConfigurationPublic?(nil))
            }
            Picker("Scheme", selection: $scheme) {
                ForEach(projectStore.project.schemes, id: \.self) { scheme in
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
                LoadingButton(isLoading: devicesStore.loadingDevices, action: {
                    Task { await devicesStore.loadDevices() }
                }) {
                    Image(systemName: "arrow.clockwise")
                }
                Picker("Devices", selection: $device) {
                    ForEach(devicesStore.devices, id: \.id) { device in
                        Text("\(device.deviceName) (\(device.udid))")
                            .tag(device)
                    }
                    Divider().tag(Components.Schemas.DeviceWithStatus?(nil))
                }
            }
            if let device = self.device, !(device.connected ?? false) {
                Text("Device is not connected")
                    .bold()
                    .foregroundStyle(.orange)
            }
            
            HStack {
                Button("Cancel") {
                    dismiss()
                }.disabled(buildsStore.addingBuild)
                Spacer()
                LoadingButton(isLoading: buildsStore.addingBuild, action: {
                    Task {
                        defer { dismiss() }
                        
                        await buildsStore.addBuild(
                            data: .init(
                                configuration: configuration!.name,
                                deviceId: device!.id,
                                scheme: scheme!.name,
                                testPlan: testPlan!.name
                            )
                        )
                    }
                }) {
                    Text("Start Build")
                }.disabled(
                    configuration == nil ||
                    scheme == nil ||
                    testPlan == nil ||
                    device == nil || !(device?.connected ?? false)
                )
            }
        }
        .padding(20)
    }
}

#Preview {
    AddBuildView()
        .environmentObject(BuildsStore(projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
        .environmentObject(DevicesStore(apiClient: MockAPIClient()))
        .environmentObject(ProjectStore(project: Components.Schemas.XcProjectPublic.mock))
}
