//
//  LottieAnimationView.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI
import Lottie

struct LottieAnimationView: View {
    @State private var isPlaying = false
    
    let animation = LottieAnimation.named("Favorite App Icon")
    
    var body: some View {
        BaseScreenView(routeSetting: lottieAnimationSetting) {
            VStack(alignment: .center, spacing: 16) {
                Spacer()
                LottieView(animation: animation)
                    .resizable()
                    .playbackMode(isPlaying ? .playing(.fromFrame(animation!.startFrame, toFrame: animation!.endFrame, loopMode: .loop)) : .paused)
                    .aspectRatio(1, contentMode: .fit)
                CustomButton("Toggle Play") {
                    isPlaying.toggle()
                }
                Spacer()
            }
        }
        .onAppear {
            print("Appeared: \"LottieAnimation\"")
        }
    }
}

#Preview {
    LottieAnimationView()
}
