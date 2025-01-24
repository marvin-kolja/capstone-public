//
//  TwoColumnView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct TwoColumnView<Content: View, Detail: View>: View {
    @ViewBuilder var content: () -> Content
    @ViewBuilder var detail: () -> Detail
    
    var body: some View {
        VStack {
            HSplitView {
                VStack{
                    Spacer()
                    HStack{
                        Spacer()
                        content()
                        Spacer()
                    }
                    Spacer()
                }
                .frame(minWidth: 200, maxWidth: 200)
                VStack{
                    Spacer()
                    HStack{
                        Spacer()
                        detail()
                        Spacer()
                    }
                    Spacer()
                }
                .frame(minWidth: 200)
            }.disabled(true)
        }
    }
}

#Preview {
    TwoColumnView( content: {
        Text("Content")
    }, detail: {
        Text("Detail")
    })
}
