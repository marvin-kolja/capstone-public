//
//  TestPlanConfigForm.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct TestPlanConfigForm: View {
    @Binding var data: TestPlanFormData
    var availableXcTestPlans: [String]

    var body: some View {
        Form {
            TextField("Name", text: $data.name)

            Divider()

            Picker(selection: $data.xcTestPlanName) {
                if let defaultXcTestPlan = data.defaultXcTestPlanName, !availableXcTestPlans.contains(defaultXcTestPlan) {
                    Text(defaultXcTestPlan)
                        .tag(defaultXcTestPlan)
                }

                ForEach(availableXcTestPlans, id: \.self) { xcTestPlan in
                    Text(xcTestPlan)
                }
            } label: {
                HStack {
                    Text("Xc Test Plan")
                    if !availableXcTestPlans.contains(data.xcTestPlanName) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                            .help("Unable to find '\(data.xcTestPlanName)' in any of the builds.")
                    }
                }
            }

            Divider()

            Picker("Recording Start Strategy", selection: $data.recordingStartStrategy) {
                ForEach(Components.Schemas.RecordingStartStrategy.allCases, id: \.self) { strategy in
                    Text(strategy.rawValue.capitalized).tag(strategy)
                }
            }

            Picker("Recording Strategy", selection: $data.recordingStrategy) {
                ForEach(Components.Schemas.RecordingStrategy.allCases, id: \.self) { strategy in
                    Text(strategy.rawValue.replacingOccurrences(of: "_", with: " ").capitalized)
                        .tag(strategy)
                }
            }

            LabeledContent("Metrics") {
                MetricPickerView(selectedMetrics: $data.metrics)
            }

            Divider()

            Stepper(value: $data.repetitions, in: 1...10) {
                Text("Repetitions: \(data.repetitions)")
            }
            Picker("Repetition Strategy", selection: $data.repetitionStrategy) {
                ForEach(Components.Schemas.RepetitionStrategy.allCases, id: \.self) { strategy in
                    Text(strategy.rawValue.replacingOccurrences(of: "_", with: " ").capitalized)
                        .tag(strategy)
                }
            }
            Toggle("End on Failure", isOn: $data.endOnFailure)
            Toggle("Reinstall App", isOn: $data.reinstallApp)
        }
    }
}

#Preview {
    @Previewable @State var data = TestPlanFormData.fromExisting(testPlan: Components.Schemas.SessionTestPlanPublic.mock)

    TestPlanConfigForm(data: $data, availableXcTestPlans: [
        "Xc test plan",
        "Another Xc test plan"
    ])
}
