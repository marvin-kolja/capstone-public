//
//  PerformanceChartSection.swift
//  Client
//
//  Created by Marvin Willms on 28.01.25.
//

import SwiftUI

struct PerformanceChartSection: View {
    let metric: Components.Schemas.Metric
    var traceResult: Components.Schemas.TraceResultPublic?
    
    @State var isExpanded = false
    
    var body: some View {
        Section(isExpanded: $isExpanded) {
            VStack(alignment: .center) {
                
                if let traceResult = traceResult {
                    switch metric {
                    case .cpu:
                        PerformanceChart(data: traceResult.cpuChartData, yFormat: .percent, yTitel: "CPU", markType: .line)
                    case .gpu:
                        PerformanceChart(data: traceResult.gpuChartData, yFormat: .percent, yTitel: "GPU", markType: .line)
                    case .fps:
                        PerformanceChart(data: traceResult.fpsChartData, yFormat: .fps, yTitel: "FPS", markType: .bar)
                    case .memory:
                        PerformanceChart(data: traceResult.memoryChartData, yFormat: .mb, yTitel: "Memory", markType: .line)
                    }
                } else {
                    Text("No Data")
                }
                
            }
            .padding()
            .frame(maxWidth: .infinity)
            .frame(height: 200)
        } header: {
            HStack {
                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 8, height: 8)
                    .bold()
                
                Text(metric.rawValue.uppercased())
                    .font(.subheadline)
            }
            .contentShape(Rectangle())
            .onTapGesture {
                isExpanded.toggle()
            }
        }
    }
}

#Preview {
    PerformanceChartSection(
        metric: .cpu,
        traceResult: nil
    )
}
