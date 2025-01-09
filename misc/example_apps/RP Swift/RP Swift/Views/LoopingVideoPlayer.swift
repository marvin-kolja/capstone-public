//
//  LoopingVideoPlayer.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//
//  Inspired by https://stackoverflow.com/a/77100697
//

import SwiftUI
import AVKit

struct LoopingVideoPlayer: View {
    var player: AVQueuePlayer
    private var playerLooper: AVPlayerLooper
    
    var body: some View {
        VideoPlayer(player: player)
            .onDisappear{ player.pause() }
    }
    
    init(player: AVQueuePlayer) {
        self.player = player
        playerLooper = AVPlayerLooper(player: player, templateItem: player.currentItem!)
    }
}

#Preview {
    let url = URL(string: "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4")!
    let asset = AVAsset(url: url)
    let item = AVPlayerItem(asset: asset)
    
    let player = AVQueuePlayer(playerItem: item)
    
    return LoopingVideoPlayer(player: player)
        .disabled(true) // Hides iOS video controls
        .aspectRatio(contentMode: .fit)
        .frame(maxWidth: .infinity)
}
