//
//  RotatingImageView.swift
//  RP Swift
//
//  Created by Marvin Willms on 14.05.24.
//

import SwiftUI

struct RotatingImageView<Content: View>: View {
    let content: Content
    @Binding var isRotating: Bool
    @State var rotationDegree: Double = 0
    

    init(isRotating: Binding<Bool>, @ViewBuilder content: () -> Content) {
        self.content = content()
        self._isRotating = isRotating
    }

    var body: some View {
        content
            .rotationEffect(.degrees(isRotating ? 360 : 360))
            .onAppear {
                print("Image appeared")
                rotationDegree = 360
            }
    }
}

#Preview {
    @State var isRotating = false
    
    return RotatingImageView(isRotating: $isRotating) {
        Image("IMG_0001")
            .onAppear {
                withAnimation(Animation.linear(duration: 10).repeatForever(autoreverses: false)) {
                    isRotating = true
                }
            }
    }
}
