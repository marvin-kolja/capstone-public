//
//  BuildsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct BuildsView: View {
    var body: some View {
        TwoColumnView(content: {
            List {
                
            }.nostyle()
        }, detail: {
            BuildDetailView()
        })
    }
}

#Preview {
    BuildsView()
}
