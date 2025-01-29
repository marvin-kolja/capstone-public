//
//  ServerStatusBadge.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

/// Creates a badge reflecting the current server status
struct ServerStatusBadge: View {
    var status: ServerStatus

    private var systemImage: String {
        switch status {
        case .down:
            return "exclamationmark.octagon.fill"
        case .healthy:
            return "checkmark.circle.fill"
        case .unhealty:
            return "exclamationmark.triangle.fill"
        case .unknown:
            return "questionmark.circle.fill"
        }
    }

    private var color: Color {
        switch status {
        case .down:
            return .red
        case .healthy:
            return .green
        case .unhealty:
            return .orange
        case .unknown:
            return .gray
        }
    }

    var body: some View {
        Image(systemName: systemImage)
            .foregroundColor(color)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            ServerStatusBadge(status: .down(error: nil))
                .previewDisplayName("Down")
            ServerStatusBadge(status: .unhealty)
                .previewDisplayName("Unhealthy")
            ServerStatusBadge(status: .healthy)
                .previewDisplayName("Healthy")
            ServerStatusBadge(status: .unknown)
                .previewDisplayName("Unknown")
        }
        .previewLayout(PreviewLayout.sizeThatFits)
        .padding()
    }
}
