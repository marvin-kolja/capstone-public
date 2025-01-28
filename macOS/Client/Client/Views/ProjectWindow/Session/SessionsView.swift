//
//  SessionsView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import SwiftUI

struct SessionsView: View {
    @EnvironmentObject var sessionStore: SessionStore

    @State var selectedSessionId: String?
    @State var isStartingSession = false
    
    var sortedSessions: [Components.Schemas.TestSessionPublic] {
        return sessionStore.sessions.sorted(by: { $0.createdAt.compare($1.createdAt) == .orderedDescending })
    }

    var body: some View {
        TwoColumnView(content: {
            LoadingView(isLoading: sessionStore.loadingSessions, hasData: !sessionStore.sessions.isEmpty, refresh: {
                Task {
                    await sessionStore.loadSessions()
                }
            }) {
                ZStack {
                    List(sortedSessions, id: \.id, selection: $selectedSessionId) { session in
                        HStack {
                            Text(session.planSnapshot.name)
                            Spacer()
                            Text(session.createdAt.formatted())
                        }.tag(session.id)
                    }
                    .listStyle(.sidebar)
                    .scrollContentBackground(.hidden)
                    if (sessionStore.sessions.isEmpty) {
                        Text("No Sessions")
                    }
                }
            }
        }, detail: {
            if let sessionId = selectedSessionId, let session = sessionStore.getSessionById(sessionId) {
                SessionDetailView(session: session)
            } else {
                Button("Start new Session", action: { isStartingSession = true })
            }
        })
        .task { await sessionStore.loadSessions() }
        .toolbar {
            Button(action: { isStartingSession = true }) {
                Image(systemName: "plus")
            }
        }
        .sheet(isPresented: $isStartingSession) {
            AddSessionView()
        }
    }
}

#Preview {
    SessionsView()
        .environmentObject(SessionStore(projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
}
