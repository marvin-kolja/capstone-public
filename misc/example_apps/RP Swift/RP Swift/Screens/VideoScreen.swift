//
//  VideoScreen.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI
import AVFoundation
import AVKit

struct VideoScreen: View {
    @State private var player: AVQueuePlayer?
    
    init() {
        self.player = nil
    }
    
    var body: some View {
        BaseScreenView(routeSetting: videoScreenSetting) {
            VStack(alignment: .center, spacing: 16) {
                Spacer()
                if let player = player {
                    LoopingVideoPlayer(player: player)
                        .disabled(true) // Hides iOS video
                        .aspectRatio(16/9, contentMode: .fit)
                        .frame(maxWidth: .infinity)
                        .onAppear {
                            player.isMuted = true
                        }
                }
                CustomButton("Toggle Play") {
                    guard player?.status == AVPlayer.Status.readyToPlay else {
                        return;
                    }
                    
                    if (player?.timeControlStatus == .playing) {
                        player?.pause()
                    } else {
                        
                        player?.play()
                    }
                }
                Spacer()
            }
        }
        .onAppear {
            print("Appeared: \"Video\"")
            
            let url = Bundle.main.url(forResource: "bee", withExtension: "mp4")!
            let asset = AVAsset(url: url)
            let item = AVPlayerItem(asset: asset)
            
            self.player = AVQueuePlayer(playerItem: item)
        }
    }
}

#Preview {
    VideoScreen()
}
