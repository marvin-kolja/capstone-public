//
//  RP_SwiftApp.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI

@main
struct RP_SwiftApp: App {
    var body: some Scene {
        WindowGroup {
            ScreenRecordingProvider(controller: ScreenRecordingController()) {
                ContentView()
            }
        }
    }
}
