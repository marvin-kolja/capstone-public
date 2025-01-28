//
//  ExecutionStepView.swift
//  Client
//
//  Created by Marvin Willms on 28.01.25.
//

import SwiftUI

struct ExecutionStepView: View {
    let step: Components.Schemas.ExecutionStepPublic
    let stepIndex: Int

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            TestStatusIcon(status: step.status?.rawValue)
                .frame(width: 24, height: 24)

            VStack(alignment: .leading) {
                HStack {
                    Text("Step \(stepIndex + 1)")
                        .font(.headline)
                    Spacer()
                    Text(formattedDate(step.updatedAt))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Divider()

                Grid(alignment: .leading) {
                    GridRow {
                        Text("Metrics:")
                            .bold()
                        ForEach(step.metrics, id: \.rawValue) { metric in
                            Text(metric.rawValue.uppercased())
                        }
                    }

                    GridRow {
                        Text("Recording")
                            .bold()
                        Text(step.recordingStartStrategy.rawValue.capitalized)
                    }

                    GridRow {
                        Text("Reinstall App")
                            .bold()
                        Text(step.reinstallApp ? "True" : "False")

                    }
                    GridRow {
                        Text("Test Cases:")
                            .bold()
                        ForEach(step.testCases, id: \.self) { testCase in
                            Text(testCase)
                        }
                    }
                    GridRow {
                        Text("Export Status")
                            .bold()
                        if let exportStatus = step.traceResult?.exportStatus {
                            Text(exportStatus.rawValue)
                        } else {
                            Text("Not Started")
                        }
                    }
                }.font(.subheadline)
                
                Divider()
                
                ForEach(step.metrics, id: \.self) { metric in
                    PerformanceChartSection(metric: metric, traceResult: step.traceResult)
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 8)
        .background(RoundedRectangle(cornerRadius: 10).fill(Color.gray.opacity(0.2)))
    }
}

#Preview {
    ExecutionStepView(
        step: Components.Schemas.ExecutionStepPublic.mock,
        stepIndex: 0
    )
}
