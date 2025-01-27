//
//  TestPlanStepFormSection.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

import SwiftUI

struct TestPlanStepFormSection: View {
    @EnvironmentObject var stepStore: TestPlanStepStore
    
    let step: Components.Schemas.SessionTestPlanStepPublic
    // Used as default data for the step form data
    let testPlanData: TestPlanFormData
    
    @State private var stepFormData: TestPlanStepFormData

    init(step: Components.Schemas.SessionTestPlanStepPublic, testPlanData: TestPlanFormData) {
        self.step = step
        self.testPlanData = testPlanData
        _stepFormData = State(initialValue: TestPlanStepFormData.fromExisting(step: step, testPlanData: testPlanData))
    }
    
    let availableXcTestCases = [""]
    
    var body: some View {
        CustomSection { _ in
            TestPlanStepForm(data: $stepFormData, availableXcTestCases: availableXcTestCases)
                .disabled(isUpdating || isDeleting)
                .padding()
        } label: { isExpanded in
            HStack {
                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 10, height: 10)
                    .bold()
                
                Text($stepFormData.order.wrappedValue.description)
                    .font(.title3)
                    .foregroundColor(.primary)
                Spacer()
                
                LoadingButton(isLoading: isUpdating) {
                    updateStep(data: $stepFormData.wrappedValue)
                } label: {
                    Text("Save")
                }
                .buttonStyle(.borderedProminent)
                .disabled(isDeleting)
                
                LoadingButton(isLoading: isDeleting) {
                    removeStep(id: step.id)
                } label: {
                    Label("Delete", systemImage: "trash")
                        .foregroundColor(.red)
                }
                
            }.padding()
        }
        .listRowSeparator(.hidden)
        .onChange(of: step) { old, new in
            if step.hashValue != step.hashValue {
                // Overwrite form data when step changed
                stepFormData = TestPlanStepFormData.fromExisting(step: step, testPlanData: testPlanData)
            }
        }
    }
    
    var isUpdating: Bool {
        return stepStore.updatingSteps[step.id] ?? false
    }
    
    var isDeleting: Bool {
        return stepStore.deletingSteps[step.id] ?? false
    }
    
    func updateStep(data: TestPlanStepFormData) {
        Task {
            await stepStore.update(stepId: data.id, data: data.toStepUpdate())
        }
    }

    func removeStep(id: String) {
        Task {
            await stepStore.delete(stepId: id)
        }
    }
}

#Preview {
    let projectId = Components.Schemas.SessionTestPlanPublic.mock.projectId
    let testPlanId = Components.Schemas.SessionTestPlanPublic.mock.id
    let testPlanData = TestPlanFormData.fromExisting(testPlan: Components.Schemas.SessionTestPlanPublic.mock)
    
    TestPlanStepFormSection(step: Components.Schemas.SessionTestPlanStepPublic.mock, testPlanData: testPlanData)
        .environmentObject(TestPlanStepStore(
            projectId: projectId,
            testPlanId: testPlanId,
            apiClient: MockAPIClient(),
            steps: [Components.Schemas.SessionTestPlanStepPublic.mock])
        )
}
