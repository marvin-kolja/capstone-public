//
//  TestPlansView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct TestPlansView: View {
    var body: some View {
        TwoColumnView(content: {
            List {
                
            }
        }, detail: {
            TestPlanDetailView()
        })
    }
}

#Preview {
    TestPlansView()
}
