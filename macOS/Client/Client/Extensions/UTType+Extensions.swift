//
//  UTType+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 22.01.25.
//

import UniformTypeIdentifiers

extension UTType {
    static let xcodeproj = UTType(tag: "xcodeproj", tagClass: .filenameExtension, conformingTo: .compositeContent)!
}
