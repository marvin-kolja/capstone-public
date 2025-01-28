//
//  PerformanceChart.swift
//  Client
//
//  Created by Marvin Willms on 28.01.25.
//

import SwiftUI
import Charts

struct PerformanceChartData {
    let timestamp: TimeInterval
    let value: Double
}

enum YFormat {
    case percent
    case fps
    case mb
}

enum MarkType {
    case bar
    case line
}

struct PerformanceChart: View {
    let data: [PerformanceChartData]
    let yFormat: YFormat
    let yTitel: String
    let markType: MarkType

    private let minLabels = 5
    private let maxLabels = 30

    private var maxTime: TimeInterval {
        data.map { $0.timestamp }.max() ?? 1
    }

    var body: some View {
        GeometryReader { geometry in
            let labelsCount = min(maxLabels, max(minLabels, Int(geometry.size.width / 50)))
            let secondsPerLabel = max(1, maxTime / Double(labelsCount))
            
            Chart {
                ForEach(data, id: \.timestamp) { point in
                    switch markType {
                    case .bar:
                        BarMark(
                            x: .value("Time", point.timestamp),
                            y: .value(yTitel, point.value)
                        )
                        .foregroundStyle(.blue)
                    case .line:
                        LineMark(
                            x: .value("Time", point.timestamp),
                            y: .value(yTitel, point.value)
                        )
                        .foregroundStyle(.blue)
                    }
                }
            }
            .chartScrollableAxes(.horizontal)
            .chartXVisibleDomain(length: 30 / secondsPerLabel)
            .chartXAxis {
                AxisMarks(position: .bottom, values: .stride(by: Double(Int(secondsPerLabel)))) { value in
                    if let time = value.as(TimeInterval.self) {
                        AxisValueLabel("\(Int(time))s")
                    }
                }
            }
            .padding()
            .chartYAxis {
                AxisMarks(
                    
                )
                
                switch yFormat {
                case .fps:
                    AxisMarks() { value in
                        AxisValueLabel("\(String(describing: value.as(Int.self)!)) FPS")
                    }
                case .percent:
                    AxisMarks(
                        format: Decimal.FormatStyle.Percent.percent.scale(1)
                    )
                case .mb:
                    AxisMarks() { value in
                        AxisValueLabel("\(String(describing: value.as(Int.self)!)) MB")
                    }
                }
            }
        }
    }
}

#Preview {
    PerformanceChart(data: [], yFormat: .percent, yTitel: "CPU", markType: .line)
}
