//
//  Button.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI

struct CustomButton: View {
    var label: String
    var systemImage: String?
    var action: () -> Void
    
    init (_ label: String, systemImage: String, action: @escaping () -> Void) {
        self.label = label
        self.systemImage = systemImage
        self.action = action
    }
    
    init (_ label: String, action: @escaping () -> Void) {
        self.label = label
        self.systemImage = nil
        self.action = action
    }
    
    var body: some View {
        if let systemImage = systemImage {
            Button(label, systemImage: systemImage) {
                action()
            }
            .foregroundColor(.white)
            .buttonStyle(.borderedProminent)
        } else {
            Button(label) {
                action()
            }
            .foregroundColor(.white)
            .buttonStyle(.borderedProminent)
        }
    }
}

#Preview {
    CustomButton("Test") {
        print("Hello")
    }
}
