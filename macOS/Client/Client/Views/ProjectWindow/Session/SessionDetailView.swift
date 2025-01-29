//
//  SessionDetailView.swift
//  Client
//
//  Created by Marvin Willms on 24.01.25.
//

import Charts
import SwiftUI

struct SessionDetailView: View {
    @EnvironmentObject var sessionStore: SessionStore

    let session: Components.Schemas.TestSessionPublic

    var body: some View {
        VStack(alignment: .center) {
            HStack {
                TestStatusIcon(status: session.status?.rawValue)
                Text("Session")
                    .font(.title2)
                LoadingButton(isLoading: sessionStore.cancelingSessions[session.id] ?? false) {
                    Task {
                        await sessionStore.cancelSession(sessionId: session.id)
                    }
                } label: {
                    Text("Cancel")
                }.disabled(session.status != .running)
                LoadingButton(isLoading: sessionStore.exportingSessionResults[session.id] ?? false)
                {
                    Task {
                        await sessionStore.exportSessionResults(sessionId: session.id)
                    }
                } label: {
                    Text("Process Data")
                }.disabled(session.status != .completed)
                JSONFileSaver(
                    json: session
                ) {
                    Text("Export as JSON")
                }
            }
            Divider()
            Grid(alignment: .leading) {
                GridRow {
                    Text("Build")
                        .bold()
                    Text(session.buildSnapshot.userFriendlyName)
                }
                GridRow {
                    Text("Device")
                        .bold()
                    Text(session.deviceSnapshot.deviceName)
                }
                GridRow {
                    Text("Test Plan")
                        .bold()
                    Text(session.planSnapshot.name)
                }
            }

            Text("Steps")
                .font(.title2)
            Divider()
            List {
                ForEach(session.executionSteps.indices, id: \.self) { index in
                    ExecutionStepView(step: session.executionSteps[index], stepIndex: index)
                }
            }.scrollContentBackground(.hidden)
        }
        .task {
            // TODO: Just reload the specific session
            await sessionStore.loadSessions()
            await sessionStore.streamSessionUpdates(sessionId: session.id)
        }
        .id(session.id)
    }
}

func formattedDate(_ date: Date) -> String {
    let formatter = DateFormatter()
    formatter.dateStyle = .short
    formatter.timeStyle = .short
    return formatter.string(from: date)
}

#Preview {
    SessionDetailView(session: Components.Schemas.TestSessionPublic.mock)
        .environmentObject(
            SessionStore(
                projectId: Components.Schemas.XcProjectPublic.mock.id, apiClient: MockAPIClient()))
}
