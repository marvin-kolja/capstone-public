//
//  TestPlanStepForm.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct TestPlanStepForm: View {
    @Binding var data: TestPlanStepFormData

    var availableXcTestCases: [String]

    var body: some View {
        Form {
            TextField("Name", text: $data.name)

            Divider()

            LabeledContent {
                MultiPicker(selectedOptions: $data.testCases, allOptions: availableXcTestCases)
            } label: {
                Text("Test Cases")
            }

            Divider()

            Picker("Recording Start Strategy", selection: $data.recordingStartStrategy) {
                ForEach(Components.Schemas.RecordingStartStrategy.allCases, id: \.self) {
                    strategy in
                    Text(strategy.rawValue.capitalized).tag(strategy)
                }
            }

            LabeledContent("Metrics") {
                MetricPickerView(selectedMetrics: $data.metrics)
            }

            Divider()

            Stepper(value: $data.repetitions, in: 1...10) {
                Text("Repetitions: \(data.repetitions)")
            }
            Toggle("Reinstall App", isOn: $data.reinstallApp)
        }
    }
}

#Preview {
    @Previewable @State var data = TestPlanStepFormData.fromExisting(
        step: Components.Schemas.SessionTestPlanStepPublic.mock,
        testPlanData: TestPlanFormData.fromExisting(
            testPlan: Components.Schemas.SessionTestPlanPublic.mock)
    )

    TestPlanStepForm(
        data: $data,
        availableXcTestCases: [
            "RPSwiftUI/RPSwiftUI/someTestCase"
        ])
}
