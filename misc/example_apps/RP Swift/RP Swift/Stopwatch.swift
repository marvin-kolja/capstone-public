//
//  Stopwatch.swift
//  RP Swift
//
//  Created by Marvin Willms on 15.05.24.
//

import Foundation

class Stopwatch {
    private var startTime: DispatchTime?
    private(set) var elapsed: TimeInterval = 0

    func start() {
        startTime = DispatchTime.now()
    }

    func stop() {
        guard let startTime = startTime else { return }
        let endTime = DispatchTime.now()
        let nanoTime = endTime.uptimeNanoseconds - startTime.uptimeNanoseconds
        elapsed = Double(nanoTime) / 1_000
    }

    func reset() {
        startTime = nil
        elapsed = 0
    }
}
