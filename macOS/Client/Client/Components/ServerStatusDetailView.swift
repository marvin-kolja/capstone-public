//
//  ServerStatusDetailView.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

struct ServerStatusDetailView: View {
    var isConnected: Bool
    var checkingConnection: Bool
    var onCheckConnection: () -> Void
    
    var body: some View {
        VStack(spacing: 10) {
            HStack {
                ServerStatusBadge(isConnected: isConnected)
                Text(isConnected ? "Server is Online" : "Server is Offline")
                    .font(.headline)
            }
            Divider()
            LoadingButton(isLoading: checkingConnection, action: onCheckConnection) {
                Text("Check connection")
            }
        }
        .padding()
    }
}
