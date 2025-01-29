//
//  ServerStatusDetailView.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

struct ServerStatusDetailView: View {
    @EnvironmentObject var serverStatusStore: ServerStatusStore

    var body: some View {
        VStack(spacing: 10) {
            VStack(alignment: .leading) {
                HStack {
                    ServerStatusBadge(status: serverStatusStore.serverStatus)
                    Text("Server")
                        .font(.headline)
                }
                HStack {
                    ServerStatusBadge(status: serverStatusStore.dbStatus)
                    Text("Database")
                        .font(.headline)
                }.padding(.leading, 20)
                HStack {
                    ServerStatusBadge(status: serverStatusStore.tunnelConnectStatus)
                    Text("Tunnel Connect")
                        .font(.headline)
                }.padding(.leading, 20)
            }
            Divider()
            LoadingButton(
                isLoading: serverStatusStore.checkingHealth,
                action: {
                    Task {
                        await serverStatusStore.checkHealth()
                    }
                }
            ) {
                Text("Check Health")
            }
        }
        .padding()
    }
}

#Preview {
    ServerStatusDetailView()
        .environmentObject(ServerStatusStore(apiClient: MockAPIClient()))
}
