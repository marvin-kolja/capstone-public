//
//  CoreAnimation+Extensions.swift
//  Client
//
//  Created by Marvin Willms on 28.01.25.
//

import Foundation

extension Components.Schemas.CoreAnimation {
    var timestampInterval: TimeInterval {
        return TimeInterval(timestamp) / 1_000_000_000
    }
}
