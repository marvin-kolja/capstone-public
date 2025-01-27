//
//  ManageDevicesButton.swift
//  Client
//
//  Created by Marvin Willms on 27.01.25.
//

import SwiftUI

struct ManageDevicesButton: View {
    @State var isManaging = false

    var body: some View {
        Button() {
            isManaging = true
        } label: {
            Label("Manage Devices", systemImage: "device")
        }
        .sheet(isPresented: $isManaging) {
            DevicesView()
        }
    }
}

#Preview {
    ManageDevicesButton()
}
