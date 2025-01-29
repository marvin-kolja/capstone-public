//
//  AddTestPlanView.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct AddTestPlanView: View {
    @Environment(\.dismiss) private var dismiss

    @EnvironmentObject var buildStore: BuildStore
    @EnvironmentObject var testPlanStore: TestPlanStore

    @State private var selectedBuildId: String?

    var body: some View {
        VStack(spacing: 10) {
            Text("Select a build to create a test plan")
                .font(.title2)
            Divider()
            Picker("Build", selection: $selectedBuildId) {
                ForEach(buildStore.builds, id: \.id) { build in
                    Text(build.userFriendlyName)
                        .tag(build.id)
                }
                Divider().tag(String?(nil))
            }

            if let buildId = selectedBuildId, let build = buildStore.getBuildById(buildId: buildId)
            {
                if !build.isBuildReadyForTests {
                    Text("This build is not ready for tests!")
                        .font(.headline)
                        .foregroundStyle(.orange)
                    Text("Try rebuilding & listing xc test cases...")
                        .font(.subheadline)
                        .foregroundStyle(.orange)
                }

                BuildDetailView(build: build)
                    .disabled(true)
                    .overlay(Color.gray.opacity(0.2))
            }

            LoadingButton(isLoading: testPlanStore.addingTestPlan) {
                guard let buildId = selectedBuildId else {
                    return
                }

                let data: Components.Schemas.SessionTestPlanCreate = .init(
                    buildId: buildId,
                    metrics: [],
                    name: "Test Plan \(testPlanStore.testPlans.count)",
                    projectId: testPlanStore.projectId,
                    repetitionStrategy: .entireSuite,
                    repetitions: 1
                )

                Task {
                    defer { dismiss() }

                    await testPlanStore.add(data: data)
                }
            } label: {
                Text("Add Test Plan")
            }.disabled(!(getSelectedBuild?.isBuildReadyForTests ?? false))
        }
        .task { await buildStore.loadBuilds() }
        .padding(20)
    }

    var getSelectedBuild: Components.Schemas.BuildPublic? {
        guard let buildId = selectedBuildId, let build = buildStore.getBuildById(buildId: buildId)
        else {
            return nil
        }
        return build
    }
}

#Preview {
    let projectId = Components.Schemas.XcProjectPublic.mock.id

    AddTestPlanView()
        .environmentObject(BuildStore(projectId: projectId, apiClient: MockAPIClient()))
        .environmentObject(TestPlanStore(projectId: projectId, apiClient: MockAPIClient()))
}
