//
//  TestPlansView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct TestPlansView: View {
    @EnvironmentObject var testPlanStore: TestPlanStore

    @State private var selectedTestPlanId: String?
    @State private var isAddingItem = false

    
    var body: some View {
        TwoColumnView(content: {
            LoadingView(isLoading: testPlanStore.loadingTestPlans, hasData: !testPlanStore.testPlans.isEmpty, refresh: {
                Task {
                    await testPlanStore.loadTestPlans()
                }
            }) {
                ZStack {
                    List(testPlanStore.testPlans, id: \.id, selection: $selectedTestPlanId) { testPlan in
                        HStack {
                            Text(testPlan.name)
                            Spacer()
                            LoadingButton(isLoading: testPlanStore.deletingTestPlans[testPlan.id] ?? false) {
                                Task {
                                    await testPlanStore.delete(testPlanId: testPlan.id)
                                }
                            } label: {
                                Image(systemName: "trash")
                                    .foregroundStyle(.red)
                            }
                        }.tag(testPlan.id)
                    }
                    .listStyle(.sidebar)
                    .scrollContentBackground(.hidden)
                    if (testPlanStore.testPlans.isEmpty) {
                        Text("No Test Plans")
                    }
                }
            }
        }, detail: {
            if let testPlanId = selectedTestPlanId, let testPlan = testPlanStore.getTestPlanById(testPlanId: testPlanId) {
                TestPlanDetailView(testPlan: testPlan)
                    .disabled(testPlanStore.deletingTestPlans[testPlan.id] ?? false)
                    .environmentObject(TestPlanStepStore(projectId: testPlanStore.projectId, testPlanId: testPlan.id, apiClient: testPlanStore.apiClient, steps: testPlan.steps))
            } else {
                Button("Add Test Plan", action: { isAddingItem = true })
            }
        })
        .task { await testPlanStore.loadTestPlans() }
        .toolbar {
            Button(action: { isAddingItem = true }) {
                Image(systemName: "plus")
            }
        }
        .sheet(isPresented: $isAddingItem) {
            AddTestPlanView()
        }
    }
}

#Preview {
    TestPlansView()
        .environmentObject(TestPlanStore(projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
        .environmentObject(BuildStore(projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
}
