//
//  TestPlanStepsList.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct TestPlanStepsList: View {
    @EnvironmentObject var testPlanStepStore: TestPlanStepStore

    var testPlanData: TestPlanFormData
    var availableXcTestCases: [String]

    var body: some View {
        List {
            ForEach(testPlanStepStore.steps, id: \.id) { step in
                TestPlanStepEditSection(
                    step: step,
                    testPlanData: testPlanData,
                    availableXcTestCases: availableXcTestCases
                )
                
                Divider()
            }
            
            if testPlanStepStore.steps.isEmpty {
                HStack {
                    Spacer()
                    Text("At least one Step is neccessary.")
                        .bold()
                        .foregroundStyle(.orange)
                    Spacer()
                }
            }
            
            HStack {
                Spacer()
                Button(action: {
                    addNewStep()
                }) {
                    Label("Add Step", systemImage: "plus")
                        .foregroundStyle(.primary)
                }
                .buttonStyle(.bordered)
                .disabled(availableXcTestCases.isEmpty)
                Spacer()
            }
            .padding()
            .listRowSeparator(.hidden)
        }
        .scrollContentBackground(.hidden)
        .listStyle(.plain)
    }
    
    func addNewStep() {
        let order = testPlanStepStore.steps.count
        var data = TestPlanStepFormData.fromTestPlanData(testPlanData: testPlanData, order: order)
        data.name = "Step \(order)"
        data.testCases = [availableXcTestCases[0]]
        
        Task {
            await testPlanStepStore.add(data: data.toStepCreate())
        }
    }
}

#Preview {
    TestPlanStepsList(
        testPlanData: TestPlanFormData.fromExisting(testPlan: Components.Schemas.SessionTestPlanPublic.mock),
        availableXcTestCases: ["Mock Xc Test Case"]
    ).environmentObject(
        TestPlanStepStore(
            projectId: Components.Schemas.SessionTestPlanPublic.mock.projectId,
            testPlanId: Components.Schemas.SessionTestPlanPublic.mock.id,
            apiClient: MockAPIClient(),
            steps: [Components.Schemas.SessionTestPlanStepPublic.mock]
        )
    )
}
