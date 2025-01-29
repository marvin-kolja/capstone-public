//
//  CustomSection.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct CustomSection<Label: View, Content: View>: View {

    @ViewBuilder var content: (Bool) -> Content
    @ViewBuilder var label: (Bool) -> Label

    @State private var isExpanded = true

    var body: some View {
        Section(isExpanded: $isExpanded) {
            content(isExpanded)
        } header: {
            label(isExpanded)
                .contentShape(Rectangle())
                .onTapGesture {
                    isExpanded.toggle()
                }
        }
    }
}

#Preview {
    CustomSection { isExpanded in
        Text("Some Content")
    } label: { isExpanded in
        HStack {
            Text("Some Title")
                .font(.title3)
            Spacer()
            Button {
            } label: {
                Image(systemName: "trash")
                    .foregroundStyle(.red)
            }
        }
    }
}
