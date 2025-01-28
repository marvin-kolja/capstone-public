//
//  TraceResult+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 28.01.25.
//

extension Components.Schemas.TraceResultPublic {
    var fpsChartData: [PerformanceChartData] {
        return coreAnimation.map { PerformanceChartData(timestamp: $0.timestampInterval, value:  $0.fps) }
    }
    
    var gpuChartData: [PerformanceChartData] {
        return coreAnimation.map { PerformanceChartData(timestamp: $0.timestampInterval, value:  $0.gpuUtilization) }
    }
    
    var cpuChartData: [PerformanceChartData] {
        return sysmon.map { PerformanceChartData(timestamp: $0.timestampInterval, value: $0.cpu ?? 0 ) }
    }
    
    var memoryChartData: [PerformanceChartData] {
        return sysmon.map { PerformanceChartData(timestamp: $0.timestampInterval, value: $0.memory ?? 0 ) }
    }
}
