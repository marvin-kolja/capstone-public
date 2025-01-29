//
//  MultiPicker.swift
//  Client
//
//  Created by Marvin Willms on 26.01.25.
//

import SwiftUI

struct MultiPicker: View {
    @Binding var selectedOptions: [String]
    var allOptions: [String]

    @State private var showSelector = false

    private var availableOptions: [String] {
        return allOptions.filter { !selectedOptions.contains($0) }
    }

    var body: some View {
        VStack {
            ForEach(selectedOptions.indices, id: \.self) { index in
                let option = selectedOptions[index]

                HStack {
                    if !allOptions.contains(option) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                            .help("'\(option)' is not available anymore.")
                    }
                    Text(option)
                    Spacer()
                    Button(role: .destructive) {
                        selectedOptions.remove(at: index)
                    } label: {
                        Image(systemName: "trash")
                            .foregroundColor(.red)
                    }

                }

            }.onMove { from, to in
                selectedOptions.move(fromOffsets: from, toOffset: to)
            }
            Menu {
                ForEach(availableOptions, id: \.self) { option in
                    Button {
                        selectedOptions.append(option)
                    } label: {
                        Text(option)
                    }
                }
            } label: {
                Label("Add", systemImage: "plus")
            }
            .menuStyle(.borderedButton)
            .disabled(availableOptions.isEmpty)
        }
    }
}

#Preview {
    @Previewable @State var selection: [String] = ["4"]
    var options = ["1", "2", "3"]

    MultiPicker(selectedOptions: $selection, allOptions: options).padding()
}
