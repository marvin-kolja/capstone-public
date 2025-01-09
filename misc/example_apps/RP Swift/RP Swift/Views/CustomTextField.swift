//
//  CustomTextField.swift
//  RP Swift
//
//  Created by Marvin Willms on 14.05.24.
//

import SwiftUI

struct CustomTextField: View {
    let title: String
    @Binding var text: String
    
    init(_ title: String, text: Binding<String>) {
        self.title = title
        self._text = text
    }
    
    var body: some View {
        HStack {
            Text(title)
                .frame(width: 100)
            Spacer()
            TextField(title, text: $text)
        }
    }
}

#Preview {
    @State var text: String = ""
    
    return CustomTextField("Firstname", text: $text)
}
