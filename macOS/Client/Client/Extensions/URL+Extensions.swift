//
//  URL+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 25.01.25.
//

import Foundation
import SwiftUI

extension URL {
    /// Open the url path if it's a directory or file on the systems.
    ///
    /// If it's a file it will open the parent dir and select the file.
    func showInFinder() {
        if self.hasDirectoryPath {
            NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: self.path)
        } else {
            NSWorkspace.shared.activateFileViewerSelecting([self])
        }
    }
}
