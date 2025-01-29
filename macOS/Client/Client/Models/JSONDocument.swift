//
//  JSONDocument.swift
//  Client
//
//  Created by Marvin Willms on 29.01.25.
//

import Foundation
import SwiftUI
import UniformTypeIdentifiers

struct JSONDocument: FileDocument {
    
    init(configuration: ReadConfiguration) throws {
        throw fatalError("Not supported")
    }
    static var readableContentTypes: [UTType] { [] }
    static var writableContentTypes: [UTType] { [.json] }
    
    let json: Encodable
    private let encoder: JSONEncoder
    
    init(json: Encodable) {
        self.json = json
        self.encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = .prettyPrinted
        
    }
    
    func encode() throws -> Data {
        return try self.encoder.encode(self.json)
    }
    
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper {
        let data = try self.encode()
        return FileWrapper(regularFileWithContents: data)
    }
}
