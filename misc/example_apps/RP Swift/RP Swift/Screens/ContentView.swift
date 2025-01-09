//
//  ContentView.swift
//  RP Swift
//
//  Created by Marvin Willms on 13.05.24.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var screenRecordingController: ScreenRecordingController
    @State private var path = NavigationPath()
    
    var body: some View {
        NavigationStack(path: $path) {
            BaseScreenView(routeSetting: homeSetting) {
                ZStack(alignment: .top) {
                    if screenRecordingController.finishedRendering {
                        Text("Finished Rendering")
                    }
                    VStack(alignment: .center, spacing: 16.0) {
                        Spacer()
                        TestButton()
                        ForEach(routes) { route in
                            NavButton(routeLink: route, path: $path)
                        }
                        Spacer()
                    }
                }
            }
            .environmentObject(screenRecordingController)
            .navigationDestination(for: String.self) { view in
                let route = getRouteFromPath(view)
                route?.destination($path)
            }
            .toolbar(content: {
                RecordButton()
                    .environmentObject(screenRecordingController)
            })
        }.onAppear {
            print("Appeared: \"Home\"")
        }
    }
    
    func getRouteFromPath(_ path: String) -> RouteLink? {
        var flatRoutes = [RouteLink]()
        for route in routes {
            flatRoutes += route.flattened()
        }
        return flatRoutes.first(where: { route in
            route.routeSetting.path == path
        })
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        @StateObject var screenRecordingController: ScreenRecordingController = MockScreenRecordingController()
        
        return ContentView()
            .environmentObject(screenRecordingController)
    }
}
