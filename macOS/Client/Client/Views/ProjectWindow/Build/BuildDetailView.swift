//
//  BuildDetailView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildDetailView: View {
    @EnvironmentObject var buildStore: BuildStore
    @EnvironmentObject var deviceStore: DeviceStore

    let build: Components.Schemas.BuildPublic

    var body: some View {
        VStack(alignment: .center) {
            HStack {
                Text("Detailed Build View")
                    .font(.title3)
                Button("Clean & Build") {
                    Task {
                        await buildStore.startBuild(buildId: build.id)
                        await buildStore.streamUpdates(buildId: build.id)
                    }
                }.disabled(
                    (buildStore.streamingBuildsUpdates[build.id] ?? false)
                        || build.status == .pending
                        || build.status == .running
                )
            }
            Divider()
            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
                GridRow {
                    Text("Status")
                        .bold()
                    Text(build.status?.rawValue ?? "unknown")
                }
                let xctestrun = build.xctestrun
                GridRow {
                    Text("Xctestrun Path")
                        .bold()
                    let xctestrunPath = xctestrun?.path
                    LocalFileLinkButton(path: xctestrunPath)
                        .disabled(xctestrunPath == nil)
                }
                GridRow {
                    Text("Test Configurations")
                        .bold()
                    Text(xctestrun?.testConfigurations.joined(separator: ", ") ?? "-")
                }
                Divider()
                GridRow {
                    Text("Device")
                        .bold()
                    Text(
                        deviceStore.getDeviceById(deviceId: build.deviceId)?.deviceName
                            ?? build.deviceId)
                }
                GridRow {
                    Text("Configuration")
                        .bold()
                    Text(build.configuration)
                }
                GridRow {
                    Text("Scheme")
                        .bold()
                    Text(build.scheme)
                }
                GridRow {
                    Text("Test Plan")
                        .bold()
                    Text(build.testPlan)
                }
                Divider()
                GridRow(alignment: .top) {
                    HStack {
                        Text("Test Cases")
                            .bold()
                        LoadingButton(isLoading: buildStore.isListingAvailableTests(build.id)) {
                            Task {
                                await buildStore.loadAvailableTests(buildId: build.id)
                            }
                        } label: {
                            Text("Load")
                        }.disabled(loadTestCasesIsDisabled)
                    }
                    ScrollView {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(build.xcTestCases ?? [], id: \.self) { xcTestCase in
                                Text(xcTestCase)
                            }
                        }
                    }
                }
            }
            Divider()
            Spacer()
        }
        .padding()
        .onAppear {
            Task { await buildStore.streamUpdates(buildId: build.id) }
            Task { await deviceStore.loadDevices() }
        }
        .id(build.id)
    }

    var deviceUsedInBuild: Components.Schemas.DeviceWithStatus? {
        return deviceStore.getDeviceById(deviceId: build.deviceId)
    }

    var loadTestCasesIsDisabled: Bool {
        guard let device = deviceUsedInBuild else {
            return true
        }
        return build.status != .success || build.xctestrun == nil || !device.isDeviceReadyForBuilds
    }
}

#Preview {
    BuildDetailView(build: Components.Schemas.BuildPublic.mock)
        .environmentObject(
            BuildStore(
                projectId: Components.Schemas.BuildPublic.mock.projectId, apiClient: MockAPIClient()
            ))
}
