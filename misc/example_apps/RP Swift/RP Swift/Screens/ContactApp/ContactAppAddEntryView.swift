//
//  ContactAppAddEntryView.swift
//  RP Swift
//
//  Created by Marvin Willms on 14.05.24.
//

import SwiftUI

struct ContactAppAddEntryView: View {
    @Binding var path: NavigationPath
    @State private var firstname: String = ""
    @State private var lastname: String = ""
    @State private var phone: String = ""
    @State private var email: String = ""
    
    var body: some View {
        BaseScreenView(routeSetting: contactAppAddEntrySetting) {
            CustomTextField("Firstname", text: $firstname)
                .keyboardType(.namePhonePad)
            CustomTextField("Lastname", text: $lastname)
                .keyboardType(.namePhonePad)
            CustomTextField("Phone", text: $phone)
                .keyboardType(.phonePad)
            CustomTextField("Email", text: $email)
                .keyboardType(.emailAddress)
            Spacer()
        }
        .textFieldStyle(.roundedBorder)
        .padding(EdgeInsets(top: 16, leading: 0, bottom: 16, trailing: 0))
        .toolbar(content: {
            Button(action: {
                path.removeLast()
            }) {
                Image(systemName: "person.crop.circle.badge.plus")
                    .foregroundColor(Color.blue)
                    .accessibilityLabel("Save")
            }
            .padding(0)
        })
        .onAppear {
            print("Appeared: \"AddEntry\"")
        }
    }
}

#Preview {
    @State var path = NavigationPath()
    return ContactAppAddEntryView(path: $path)
}
