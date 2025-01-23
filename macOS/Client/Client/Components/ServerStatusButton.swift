//
//  ServerStatusBadge.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

struct ServerStatusButton: View {
    var isConnected: Bool
    var checkingConnection: Bool
    var onCheckConnection: () -> Void
    
    @State private var showPopover: Bool = false
    
    var body: some View {
        LoadingButton(isLoading: checkingConnection, action: { showPopover.toggle() }) {
            ServerStatusBadge(isConnected: isConnected)
        }
        .popover(isPresented: $showPopover) {
            ServerStatusDetailView(isConnected: isConnected, checkingConnection: checkingConnection, onCheckConnection: onCheckConnection)
        }
    }
}

#Preview {
    ServerStatusButton(
        isConnected: true, checkingConnection: false, onCheckConnection: {}
    )
}
