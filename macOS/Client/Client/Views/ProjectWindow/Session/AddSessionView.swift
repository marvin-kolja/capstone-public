//
//  AddSessionView.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

import SwiftUI

struct AddSessionView: View {
    @Environment(\.dismiss) private var dismiss

    @EnvironmentObject var sessionStore: SessionStore
    @EnvironmentObject var testPlanStore: TestPlanStore
    @EnvironmentObject var deviceStore: DeviceStore
    @EnvironmentObject var buildStore: BuildStore

    @State var selectedTestPlanId: String?
    @State var selectedTestConfiguration: String?

    var body: some View {
        VStack(spacing: 10) {
            Text("Select a test plan to start a session")
                .font(.title2)
            Divider()
            Picker("Test Plan", selection: $selectedTestPlanId) {
                ForEach(testPlanStore.testPlans, id: \.id) { testPlan in
                    Text(testPlan.name)
                        .tag(testPlan.id)
                }
                Divider().tag(String?(nil))
            }

            if let testPlan = testPlan {
                if testPlan.steps.isEmpty {
                    Text("Test Plan requires at least 1 Step")
                        .bold()
                        .foregroundStyle(.orange)
                }
            }

            if let build = build {
                if !build.isBuildReadyForTests {
                    Text("Build is not ready for testing!")
                        .bold()
                        .foregroundStyle(.orange)
                }

                Picker("Xc Test Configuration", selection: $selectedTestConfiguration) {
                    ForEach(testConfigurations, id: \.self) { config in
                        Text(config).tag(Optional(config))
                    }
                    Divider().tag(String?(nil))
                }
            }

            if let device = device {
                if !device.isDeviceReadyForTestSession {
                    Text("Device is not ready for testing!")
                        .bold()
                        .foregroundStyle(.orange)
                }
            }

            LoadingButton(isLoading: testPlanStore.addingTestPlan) {
                startBuild()
            } label: {
                Text("Start Session")
            }.disabled(!canStartSession)
        }
        .task {
            await testPlanStore.loadTestPlans()
            await buildStore.loadBuilds()
            await deviceStore.loadDevices()
        }
        .padding(20)
    }

    func startBuild() {
        guard build != nil, let testPlan = testPlan, device != nil,
            let testConfiguration = selectedTestConfiguration
        else {
            return
        }

        let data = Components.Schemas.TestSessionCreate(
            planId: testPlan.id,
            xcTestConfigurationName: testConfiguration
        )

        Task {
            defer { dismiss() }

            await sessionStore.startSession(data: data)
        }
    }

    var isTestPlanValid: Bool {
        return !(testPlan?.steps.isEmpty ?? true)
    }

    var isBuildReady: Bool {
        return build?.isBuildReadyForTests ?? false
    }

    var isDeviceReady: Bool {
        return device?.isDeviceReadyForTestSession ?? false
    }

    var canStartSession: Bool {
        return isTestPlanValid && isBuildReady && isDeviceReady && selectedTestConfiguration != nil
    }

    var testConfigurations: [String] {
        return build?.xctestrun?.testConfigurations ?? []
    }

    var testPlan: Components.Schemas.SessionTestPlanPublic? {
        guard let testPlanId = selectedTestPlanId else {
            return nil
        }
        guard let testPlan = testPlanStore.getTestPlanById(testPlanId: testPlanId) else {
            return nil
        }
        return testPlan
    }

    var build: Components.Schemas.BuildPublic? {
        guard let testPlan = testPlan else {
            return nil
        }
        guard let build = buildStore.getBuildById(buildId: testPlan.buildId) else {
            return nil
        }
        return build
    }

    var device: Components.Schemas.DeviceWithStatus? {
        guard let build = build else {
            return nil
        }
        guard let device = deviceStore.getDeviceById(deviceId: build.deviceId) else {
            return nil
        }
        return device
    }
}

#Preview {
    AddSessionView()
}
