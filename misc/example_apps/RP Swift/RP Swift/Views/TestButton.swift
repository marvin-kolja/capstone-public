//
//  TestButton.swift
//  RP Swift
//
//  Created by Marvin Willms on 08.06.24.
//

import SwiftUI

struct TestButton: View {
    @State private var started: Bool = false
    @State private var stopwatch = Stopwatch()
    
    var body: some View {
        CustomButton(started ? "Stop Test" : "Start Test", action: {
            if started {
                print("Stopped: \"Test Trigger\"")
                stopwatch.stop()
                print("Elapsed: \(stopwatch.elapsed)")
            } else {
                print("Started: \"Test Trigger\"")
                stopwatch = Stopwatch()
                stopwatch.start()
            }
            started.toggle()
        })
        .foregroundColor(.white)
        .buttonStyle(.borderedProminent)
    }
}

#Preview {
    TestButton()
}
