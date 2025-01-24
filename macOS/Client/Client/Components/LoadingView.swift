//
//  LoadingView.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import SwiftUI

struct LoadingView<Content: View>: View {
    var isLoading: Bool
    var hasData: Bool
    var refresh: () -> Void
    @ViewBuilder var content: () -> Content
    
    var body: some View {
        VStack {
            HStack {
                Spacer()
                LoadingButton(isLoading: isLoading, action: refresh) {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.borderless)
                .padding(4)
            }
            ZStack(alignment: .center) {
                content()
                    .opacity((isLoading && !hasData) ? 0 : 1)
                    .disabled(isLoading && !hasData)
                if isLoading && !hasData {
                    ProgressView()
                        .controlSize(.small)
                }
            }
        }
    }
}

#Preview {
    LoadingView(isLoading: true, hasData: true, refresh: {
        print("Refresh")
    }) {
        Text("Some Content")
    }
}
