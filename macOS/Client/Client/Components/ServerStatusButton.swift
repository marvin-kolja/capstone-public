//
//  ServerStatusBadge.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

struct ServerStatusButton<Content: View>: View {
    var isLoading: Bool
    var serverStatus: ServerStatus

    @ViewBuilder var popoverContent: () -> Content
    @State var showPopover = false

    var body: some View {
        LoadingButton(isLoading: isLoading, action: { showPopover.toggle() }) {
            ServerStatusBadge(status: serverStatus)
        }
        .popover(isPresented: $showPopover, content: popoverContent)
    }
}

#Preview {
    ServerStatusButton(isLoading: false, serverStatus: .healthy) {
        Text("Popover")
    }
}
