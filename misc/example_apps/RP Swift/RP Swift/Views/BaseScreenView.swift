//
//  BaseScreenView.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI

struct BaseScreenView<Content: View>: View {
    @EnvironmentObject var screenRecordingController: ScreenRecordingController
    
    let routeSetting: RouteSetting
    let content: Content
    let horizontalPadding: CGFloat

    init(routeSetting: RouteSetting, @ViewBuilder content: () -> Content) {
        self.content = content()
        self.routeSetting = routeSetting
        self.horizontalPadding = 16.0
    }
    
    init(routeSetting: RouteSetting, horizontalPadding: CGFloat, @ViewBuilder content: () -> Content) {
        self.content = content()
        self.routeSetting = routeSetting
        self.horizontalPadding = horizontalPadding
    }


    var body: some View {
        let backgroundColor = screenRecordingController.isRecording ? UIColor.systemRed : UIColor.systemGray
        
        return VStack {
            content
        }
        .navigationTitle(routeSetting.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(
            Color(backgroundColor.withAlphaComponent(0.5)),
            for: .navigationBar
        )
        .toolbarBackground(
            .visible,
            for: .navigationBar
        )
        .padding(EdgeInsets(top: 0, leading: horizontalPadding, bottom: 0, trailing: horizontalPadding))
    }
}

#Preview {
    let routeSettingExample = RouteSetting(title: "Test Route", path: "test", icon: "phone")
    @StateObject var screenRecordingController: ScreenRecordingController = MockScreenRecordingController()
    return BaseScreenView(routeSetting: routeSettingExample) {
        Text("Hello")
    }.environmentObject(screenRecordingController)
}
