//
//  NavButton.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI

struct NavButton: View {
    var routeLink: RouteLink;
    @Binding var path: NavigationPath

    var body: some View {
        CustomButton(routeLink.routeSetting.title, systemImage: routeLink.routeSetting.icon) {
            print("Navigate to: \"\(routeLink.routeSetting.path)\"")
            path.append(routeLink.routeSetting.path)
        }
        .foregroundColor(.white)
        .buttonStyle(.borderedProminent)
    }
}

#Preview {
    @State var path = NavigationPath()

    return NavButton(routeLink: routes[0], path: $path)
}
