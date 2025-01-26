//
//  MetricPickerView.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct MetricPickerView: View {
    @Binding var selectedMetrics: [Components.Schemas.Metric]
    static private let allMetrics = Components.Schemas.Metric.allCases
    
    var body: some View {
        VStack(alignment: .leading) {
            ForEach(MetricPickerView.allMetrics, id: \.rawValue) { metric in
                Toggle(isOn: Binding(
                    get: { selectedMetrics.contains(metric) },
                    set: { newValue in
                        if newValue {
                            selectedMetrics.append(metric)
                        } else {
                            selectedMetrics.removeAll { $0 == metric }
                        }
                    }
                )) {
                    Text(metric.rawValue)
                }
            }
        }
    }
}

#Preview {
    @Previewable @State var metrics: [Components.Schemas.Metric] = []
    
    MetricPickerView(selectedMetrics: $metrics)
}
