//
//  AppError.swift
//  Client
//
//  Created by Marvin Willms on 23.01.25.
//

import Foundation

struct AppError: Error {
    let type: any LocalizedError

    var userMessage: String {
        var message = "\(type.failureReason ?? "Error")"
        if let recoverySuggestion = type.recoverySuggestion {
            message += "\n\(recoverySuggestion)"
        }
        return message
    }

    init(type: any LocalizedError, debugInfo: String? = nil) {
        self.type = type
        guard let debugInfo else { return }
        logger.error("\(debugInfo)")
    }
}
