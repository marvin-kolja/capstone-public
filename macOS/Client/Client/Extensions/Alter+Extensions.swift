//
//  Alter+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import SwiftUI

extension View {
    func alert(isPresented: Binding<Bool>, withError error: AppError?) -> some View {
        return alert(
            "Error",
            isPresented: isPresented,
            actions: {
                Button("Ok") {}
            }, message: {
                Text(error?.userMessage ?? "")
            }
        )
    }
}
