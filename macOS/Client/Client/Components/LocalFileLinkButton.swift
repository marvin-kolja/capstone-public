//
//  LocalFileLinkButton.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import SwiftUI

/// A `Button` that opens the given `path` in Finder, provided that it's an actual location
/// on the system disk.
///
/// The Button is link styled, uses a line limit of 1, and truncates the head.
struct LocalFileLinkButton: View {
    var path: String?

    var body: some View {
        Button(action: {
            guard let path = path else {
                return
            }
            let url = URL(fileURLWithPath: path)
            url.showInFinder()
        }) {
            Text(path ?? "-")
                .lineLimit(1)
                .truncationMode(.head)
        }
        .buttonStyle(.link)
    }
}

#Preview {
    LocalFileLinkButton(path: "/Users/")
}
