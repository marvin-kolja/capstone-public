//
//  LoadingButton.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

struct LoadingButton<Label: View>: View {
    var isLoading: Bool
    var action: @MainActor () -> Void
    @ViewBuilder var label: () -> Label
    
    @State private var showLoading = false
    
    var body: some View {
        Button(action: action) {
            ZStack {
                label()
                    .opacity(showLoading ? 0 : 1)
                if showLoading {
                    ProgressView()
                        .controlSize(.small)
                }
            }
        }
        .disabled(showLoading)
        .onChange(of: isLoading) {
            if isLoading {
                showLoading = true
            } else {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
                    if showLoading && !isLoading { showLoading = false }
                }
            }
        }
    }
}

#Preview {
    LoadingButton(isLoading: false, action: {}, label: {
        
    })
}
