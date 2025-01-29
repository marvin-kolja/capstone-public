//
//  JSONFileSaver.swift
//  Client
//
//  Created by Marvin Willms on 29.01.25.
//

import SwiftUI

enum JSONExportError: LocalizedError {
    case unexpected
    
    var failureReason: String? {
        switch self {
        case .unexpected:
            return "Unexpected error while trying to export JSON"
        }
    }
}

struct JSONFileSaver<Label: View>: View {
    let json: Encodable
    
    @ViewBuilder var label: () -> Label
    
    private let jsonDocument: JSONDocument
    @State private var isExporting = false
    @State private var exportError: AppError?
    @State private var showError = false
    
    init(json: Encodable, label: @escaping () -> Label) {
        self.json = json
        self.label = label
        self.jsonDocument = JSONDocument(json: json)
    }
    
    var body: some View {
        Button {
            isExporting = true
        } label: {
            label()
        }.fileExporter(
            isPresented: $isExporting,
            document: jsonDocument,
            contentType: .json
        ) { result in
            switch result {
            case .success(let file):
                file.absoluteURL.showInFinder()
            case .failure(let error):
                exportError = AppError(type: JSONExportError.unexpected, debugInfo: error.localizedDescription)
            }
        }.alert(isPresented: $showError, withError: exportError)
    }
}

#Preview {
    JSONFileSaver(
        json: Components.Schemas.TestSessionPublic.mock
    ) {
        Text("Export")
    }
}
