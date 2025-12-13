//
//  ContentView.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = MeetingListViewModel()
    @State private var selectedMeeting: Meeting?
    @State private var searchText = ""
    @State private var showingNewMeeting = false

    var body: some View {
        NavigationSplitView {
            // SIDEBAR
            SidebarView(selectedMeeting: $selectedMeeting)
        } detail: {
            // MAIN CONTENT
            if databaseService.isConnected {
                MeetingListView(
                    viewModel: viewModel,
                    selectedMeeting: $selectedMeeting,
                    searchText: $searchText,
                    showingNewMeeting: $showingNewMeeting
                )
            } else {
                // Database connection error
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.orange)

                    Text("Database Connection Failed")
                        .font(.title)
                        .fontWeight(.bold)

                    Text("Unable to connect to PostgreSQL database")
                        .foregroundColor(.secondary)

                    if let error = databaseService.lastError {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                            .padding()
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(8)
                    }

                    Button("Retry Connection") {
                        Task {
                            await databaseService.connect()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()
            }
        }
        .navigationTitle("Meeting Manager")
        .toolbar {
            ToolbarItem(placement: .navigation) {
                Button(action: {
                    showingNewMeeting = true
                }) {
                    Label("New Meeting", systemImage: "plus")
                }
                .disabled(!databaseService.isConnected)
            }

            ToolbarItem(placement: .primaryAction) {
                HStack {
                    // Connection status indicator
                    Circle()
                        .fill(databaseService.isConnected ? Color.green : Color.red)
                        .frame(width: 8, height: 8)

                    Text(databaseService.isConnected ? "Connected" : "Disconnected")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .task {
            // Connect to database on launch
            await databaseService.connect()

            if databaseService.isConnected {
                await viewModel.loadMeetings()
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(DatabaseService.shared)
}
