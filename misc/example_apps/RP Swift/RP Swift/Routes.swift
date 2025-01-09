//
//  Routes.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import Foundation
import SwiftUI

struct RouteSetting: Identifiable {
    let id = UUID()
    let title: String
    let path: String
    let icon: String
}

struct RouteLink: Identifiable {
    let id = UUID()
    let routeSetting: RouteSetting
    let destination: (_ path: Binding<NavigationPath>) -> AnyView
    let routes: [RouteLink]?
    
    init(routeSetting: RouteSetting, destination: @escaping (_: Binding<NavigationPath>) -> AnyView) {
        self.routeSetting = routeSetting
        self.destination = destination
        self.routes = nil
    }
    
    init(routeSetting: RouteSetting, routes: [RouteLink], destination: @escaping (_: Binding<NavigationPath>) -> AnyView) {
        self.routeSetting = routeSetting
        self.destination = destination
        self.routes = routes
    }
}

extension RouteLink {
    func flattened() -> [RouteLink] {
        var flatList = [self]
        if let routes = routes {
            for route in routes {
                flatList += route.flattened()
            }
        }
        return flatList
    }
}

let lottieAnimationSetting = RouteSetting(title: "Lottie Animation", path: "animation", icon: "star.fill")

let homeSetting = RouteSetting(title: "Home", path: "home", icon: "house")

let videoScreenSetting = RouteSetting(title: "Video Screen", path: "video", icon: "play.rectangle.fill")

let gallerySetting = RouteSetting(title: "Gallery", path: "gallery", icon: "photo.on.rectangle")

let contactAppHomeSetting = RouteSetting(title: "Contact App", path: "contact_app/home", icon: "person.2.fill")

let contactAppAddEntrySetting = RouteSetting(title: "Add Entry", path: "contact_app/add_entry", icon: "plus.circle")
let contactAppAddEntry = RouteLink(routeSetting: contactAppAddEntrySetting, destination: { path in AnyView(ContactAppAddEntryView(path: path)) })

let routes = [
    RouteLink(routeSetting: lottieAnimationSetting, destination: { _ in AnyView(LottieAnimationView()) }),
    RouteLink(routeSetting: videoScreenSetting, destination: { _ in
        AnyView(VideoScreen()) }),
    RouteLink(routeSetting: gallerySetting, destination: { _ in AnyView(GalleryView()) }),
    RouteLink(routeSetting: contactAppHomeSetting, routes: [contactAppAddEntry], destination: { path in AnyView(ContactAppHomeView(path: path)) }),
]
