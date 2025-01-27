//
//  TestPlanDetailView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

enum TestPlanPage {
    case testConfig
    case steps
}

struct TestPlanDetailView: View {
    @EnvironmentObject var buildsStore: BuildStore
    @EnvironmentObject var testPlanStore: TestPlanStore
    @EnvironmentObject var testPlanStepStore: TestPlanStepStore

    var testPlan: Components.Schemas.SessionTestPlanPublic

    @State private var testPlanData: TestPlanFormData

    init(testPlan: Components.Schemas.SessionTestPlanPublic) {
        _testPlanData = State(initialValue: TestPlanFormData.fromExisting(testPlan: testPlan))
        self.testPlan = testPlan
    }

    @State private var selectedPage: TestPlanPage = .testConfig

    var body: some View {
        VStack {
            Picker("", selection: $selectedPage, content: {
                Text("Test Config")
                    .tag(TestPlanPage.testConfig)
                Text("Steps")
                    .tag(TestPlanPage.steps)
            }).pickerStyle(.palette)
            VStack{
                switch selectedPage {
                case .testConfig:
                    VStack {
                        ScrollView {
                            TestPlanConfigForm(data: $testPlanData)
                                .disabled(testPlanStore.updatingTestPlans[testPlan.id] ?? false)
                        }
                        HStack {
                            Spacer()
                            LoadingButton(isLoading: testPlanStore.updatingTestPlans[testPlan.id] ?? false) {
                                Task {
                                    await testPlanStore.update(testPlanId: testPlan.id, data: testPlanData.toTestPlanUpdate())
                                }
                            } label: {
                                Text("Save Config")
                            }
                            .buttonStyle(.borderedProminent)
                            
                        }.padding(.bottom, 4)
                    }
                case .steps:
                    TestPlanStepsList(
                        testPlanData: testPlanData,
                        availableXcTestCases: availableXcTestCases
                    )
                }
            }.padding()
            Spacer()
        }
        .padding()
        .task { await buildsStore.loadBuilds() }
    }
    
    var availableXcTestCases: [String] {
        return buildsStore.getBuildById(buildId: testPlan.buildId)?.xcTestCases ?? []
    }
}

#Preview {
    TestPlanDetailView(testPlan: Components.Schemas.SessionTestPlanPublic.mock)
        .environmentObject(BuildStore(projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
        .environmentObject(TestPlanStore(projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
}
