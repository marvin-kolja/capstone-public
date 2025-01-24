//
//  SessionsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct SessionsView: View {
    var body: some View {
        TwoColumnView(content: {
            List {
                
            }.nostyle()
        }, detail: {
            SessionDetailView()
        })
    }
}

#Preview {
    SessionsView()
}
