//
//  ServerStatusBadge.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

struct ServerStatusBadge: View {
    var isConnected: Bool
    
    var body: some View {
        Image(systemName: isConnected ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
            .foregroundColor(isConnected ? .green : .red)
    }
}
