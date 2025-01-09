//
//  Recorder.swift
//  RP Swift
//
//  Created by Marvin Willms on 15.05.24.
//

import SwiftUI
import Combine
import Photos
import ReplayKit

//extension RPScreenRecorder {
//    func startRecordingAsync() async throws {
//        return try await withCheckedThrowingContinuation { continuation in
//            startRecording { error in
//                if let error = error {
//                    continuation.resume(throwing: error)
//                } else {
//                    continuation.resume(returning: ())
//                }
//            }
//        }
//    }
//    
//    func stopRecordingAsync(_ url: URL) async throws {
//        return try await withCheckedThrowingContinuation { continuation in
//            stopRecording(withOutput: url) { error in
//                if let error = error {
//                    continuation.resume(throwing: error)
//                } else {
//                    continuation.resume(returning: ())
//                }
//            }
//        }
//    }
//}

class ScreenRecordingController: ObservableObject {
    @Published private(set) var isRecording = false
    @Published private(set) var finishedRendering = false

    func startRecordingDelegate() {
        let stopwatch = Stopwatch()
        stopwatch.start()
        
        startRecording { result in
            stopwatch.stop()
            print("startRecording took \(stopwatch.elapsed)")
            
            guard result else {
                return
            }
            
            DispatchQueue.main.async {
                self.isRecording = result
                self.finishedRendering = false
            }
        }
    }

    func stopRecordingDelegate(saveInPhotos save: Bool = false, handler: @escaping (URL?, ((any Error)?)) -> Void) {
        DispatchQueue.main.async {
            self.isRecording = false
        }
        let stopwatch = Stopwatch()
        stopwatch.start()
        stopRecording { result, error in
            stopwatch.stop()
            print("stopRecording took \(stopwatch.elapsed)")
            
            guard let result = result else {
                handler(nil, error)
                return
            }
            
            DispatchQueue.main.async {
                self.finishedRendering = true
            }
            if save {
                self.writeVideoToPhotoLibrary(result.path())
            }
            handler(result, nil)
        }
    }
    
    func writeVideoToPhotoLibrary(_ path: String) {
        let url = URL(fileURLWithPath: path)
        PHPhotoLibrary.shared().performChanges({ _ = PHAssetChangeRequest.creationRequestForAssetFromVideo(atFileURL: url)!})
    }

    func startRecording(handler: @escaping (Bool) -> Void) {
        RPScreenRecorder.shared().startRecording { error in
            if let error = error {
                return handler(false)
            } else {
                return handler(true)
            }
        }
    }

    func stopRecording(handler: @escaping (URL?, ((any Error)?)) -> Void) {
        let videoOutputURL = FileManager.default.temporaryDirectory.appendingPathComponent("\(UUID()).mp4")
        
        RPScreenRecorder.shared().stopRecording(withOutput: videoOutputURL) { error in
            if let error = error {
                handler(nil, error)
            } else {
                handler(videoOutputURL, nil)
            }
        }
    }
}

class MockScreenRecordingController: ScreenRecordingController {
    override func startRecording(handler: @escaping (Bool) -> Void) {
        return handler(true)
    }
    
    override func stopRecording(handler: @escaping (URL?, ((any Error)?)) -> Void) {
        return handler(URL(fileURLWithPath: "non existing path"), nil)
    }
}

struct ScreenRecordingProvider<Content: View>: View {
    @StateObject var controller: ScreenRecordingController
    let content: Content

    init(controller: ScreenRecordingController, @ViewBuilder content: () -> Content) {
        _controller = StateObject(wrappedValue: controller)
        self.content = content()
    }

    var body: some View {
        content
            .environmentObject(controller)
    }
}
