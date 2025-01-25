//
//  URL+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import Foundation
import SwiftUI

extension URL {
    /// Open the path and select the folder or file
    ///
    /// If the path does not exist it will do nothing
    func showInFinder() {
        NSWorkspace.shared.activateFileViewerSelecting([self])
    }
}
