//
//  BuildDetailView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildDetailView: View {
    @EnvironmentObject var buildsStore: BuildsStore
    @ObservedObject var buildStore: BuildStore

    var body: some View {
        VStack(alignment: .center) {
            HStack {
                Text("Detailed Build View")
                    .font(.title3)
                Button("Clean & Build") {
                    Task {
                        await buildStore.startBuild()
                        await buildStore.streamUpdates()
                    }
                }.disabled(
                    buildStore.streamingUpdates ||
                    buildStore.build.status == .pending ||
                    buildStore.build.status == .running
                )
            }
            Divider()
            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
                GridRow {
                    Text("Status")
                        .bold()
                    Text(buildStore.build.status?.rawValue ?? "unknown")
                }
                let xctestrun = buildStore.build.xctestrun
                GridRow {
                    Text("Xctestrun Path")
                        .bold()
                    let xctestrunPath = xctestrun?.path
                    Button(action: {
                        guard let path = xctestrunPath else {
                            return
                        }
                        let url = URL(fileURLWithPath: path)
                        url.showInFinder()
                    }) {
                        Text(xctestrunPath ?? "-")
                            .lineLimit(1)
                            .truncationMode(.head)
                    }
                    .buttonStyle(.link)
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
                    Text(buildStore.build.deviceId)
                }
                GridRow {
                    Text("Configuration")
                        .bold()
                    Text(buildStore.build.configuration)
                }
                GridRow {
                    Text("Scheme")
                        .bold()
                    Text(buildStore.build.scheme)
                }
                GridRow {
                    Text("Test Plan")
                        .bold()
                    Text(buildStore.build.testPlan)
                }
            }
            Divider()
            Spacer()
        }
        .padding()
        .onAppear { Task { await buildStore.streamUpdates() } }
        .id(buildStore.build.id)
    }
}

#Preview {
    BuildDetailView(buildStore: BuildStore(projectId: Components.Schemas.BuildPublic.mock.projectId, apiClient: MockAPIClient(), build: Components.Schemas.BuildPublic.mock))
}
