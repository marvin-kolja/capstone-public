//
//  TestStatusIcon.swift
//  Client
//
//  Created by Marvin Willms on 28.01.25.
//

import SwiftUI

struct TestStatusIcon: View {
    let status: String?

    var body: some View {
        if status == "running" {
            ProgressView()
                .controlSize(.small)
        } else {
            Image(systemName: systenName)
                .foregroundColor(statusColor)
        }
    }

    var systenName: String {
        switch status {
        case "completed":
            return "checkmark.circle.fill"
        case "failed":
            return "xmark.circle.fill"
        case "cancelled":
            return "exclamationmark.circle.fill"
        default:
            return "questionmark.circle.fill"
        }
    }

    var statusColor: Color {
        switch status {
        case "running":
            return .blue
        case "completed":
            return .green
        case "failed":
            return .red
        case "cancelled":
            return .orange
        default:
            return .gray
        }
    }
}

#Preview {
    TestStatusIcon(status: "running")
}
