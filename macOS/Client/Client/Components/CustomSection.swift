//
//  CustomSection.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct CustomSection<Label: View, Content: View>: View {

    @ViewBuilder var content: () -> Content
    @ViewBuilder var label: () -> Label

    @State private var isExpanded = true

    var body: some View {
        Section(isExpanded: $isExpanded) {
            content()
        } header: {
            label()
            .contentShape(Rectangle())
            .onTapGesture {
                isExpanded.toggle()
            }
        }
    }
}

#Preview {
    CustomSection {
        Text("Some Content")
    } label: {
        HStack {
            Text("Some Title")
                .font(.title3)
            Spacer()
            Button { } label : {
                Image(systemName: "trash")
                    .foregroundStyle(.red)
            }
        }
    }
}
