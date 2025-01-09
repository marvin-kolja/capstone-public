//
//  RecordButton.swift
//  RP Swift
//
//  Created by Marvin Willms on 15.05.24.
//

import SwiftUI

struct RecordButton: View {
    @EnvironmentObject var screenRecordingController: ScreenRecordingController

    var body: some View {
        let icon: Image
        let color: Color
        let label: String

        if screenRecordingController.isRecording {
            icon = Image(systemName: "stop.circle")
            color = Color.red
            label = "Stop Recording"
        } else {
            icon = Image(systemName: "record.circle")
            color = Color.gray
            label = "Start Recording"
        }
        
        return Button(action: {
            if screenRecordingController.isRecording {
                screenRecordingController.stopRecordingDelegate(saveInPhotos: false) { url, error  in
                    
                }
            } else {
                screenRecordingController.startRecordingDelegate()
            }
        }) {
            icon
                .foregroundColor(color)
                .accessibilityLabel(label)
        }
        .padding(0)
    }
}

#Preview {
    @StateObject var screenRecordingController: ScreenRecordingController = MockScreenRecordingController()
    
    return RecordButton().environmentObject(screenRecordingController)
}
