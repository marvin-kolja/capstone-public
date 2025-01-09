//
//  GalleryView.swift
//  RP Swift
//
//  Created by Marvin Willms on 14.05.24.
//

import SwiftUI

let nativeImages = [
    Image("IMG_0001"),
    Image("IMG_0002"),
    Image("IMG_0003"),
    Image("IMG_0004"),
    Image("IMG_0005"),
]

struct GalleryView: View {
    static private let spacing: CGFloat = 4
    
    private let columnGrid = [
        GridItem(.flexible(), spacing: GalleryView.spacing),
        GridItem(.flexible(), spacing: GalleryView.spacing),
        GridItem(.flexible(), spacing: GalleryView.spacing),
        GridItem(.flexible(), spacing: GalleryView.spacing),
    ]
    
    @State private var rotationDegrees = 0.0
    
    let timer = Timer.publish(every: 0.02, on: .main, in: .common).autoconnect()
    
    var body: some View {
        BaseScreenView(routeSetting: gallerySetting, horizontalPadding: 0) {
            ScrollView {
                LazyVGrid(columns: columnGrid, spacing: GalleryView.spacing) {
                    ForEach(0..<400, id: \.self) { i in
                        nativeImages[i % nativeImages.count]
                            .resizable()
                            .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity)
                            .clipped()
                            .aspectRatio(1, contentMode: .fit)
                            .rotationEffect(.degrees(rotationDegrees))
                    }
                }
            }
            .onAppear {
                rotationDegrees = 0
            }
            .onReceive(timer) { _ in
                rotationDegrees += (360/500)
                if rotationDegrees >= 360 {
                    rotationDegrees = rotationDegrees - 360
                }
            }
        }.onAppear {
            print("Appeared: \"Gallery\"")
        }
    }
}

#Preview {
    GalleryView()
}
