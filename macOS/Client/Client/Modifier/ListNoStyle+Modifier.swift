//
//  ListNoStyle+Modifier.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct ListNoStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .listStyle(.plain)
            .background(Color.clear)
            .scrollContentBackground(.hidden)
    }
}

extension View {
    /// Removes styles from a normal List
    func nostyle() -> some View {
        modifier(ListNoStyle())
    }
}
