//
//  ContactAppHomeView.swift
//  RP Swift
//
//  Created by Marvin Willms on 14.05.24.
//

import SwiftUI

struct ContactAppHomeView: View {
    @Binding var path: NavigationPath
    @State private var contacts = (0..<200).map {
        return "\($0 + 1) Firstname Lastname \n0043 1234567 \($0 + 1)"
    }
    
    var body: some View {
        BaseScreenView(routeSetting: contactAppHomeSetting, horizontalPadding: 0) {
            List {
                ForEach($contacts, id: \.self) { $contact in
                    HStack(alignment: .center) {
                        Text(contact)
                        Spacer()
                        Image(systemName: "phone")
                    }
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            contacts.removeAll { element in
                                return element == contact
                            }
                            print(contacts[0])
                        } label: {
                            Label("delete", systemImage: "trash.fill")
                        }
                    }
                }
            }
            .listStyle(.inset)
            .toolbar(content: {
                Button(action: {
                    path.append(contactAppAddEntry.routeSetting.path)
                }) {
                    Image(systemName: contactAppAddEntry.routeSetting.icon)
                        .foregroundColor(Color.blue)
                        .accessibilityLabel(contactAppAddEntry.routeSetting.title)
                }
                .padding(0)
            })
        }.onAppear {
            print("Appeared: \"ContactApp\"")
        }
    }
}

#Preview {
    @State var path = NavigationPath()
    return ContactAppHomeView(path: $path)
}
