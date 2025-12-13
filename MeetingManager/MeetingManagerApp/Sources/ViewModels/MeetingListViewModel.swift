//
//  MeetingListViewModel.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//

import Foundation
import SwiftUI

@MainActor
class MeetingListViewModel: ObservableObject {
    @Published var meetings: [Meeting] = []
    @Published var isLoading: Bool = false
    @Published var error: String?

    private let databaseService = DatabaseService.shared

    var upcomingMeetings: [Meeting] {
        meetings.filter { $0.isUpcoming }
    }

    var pastMeetings: [Meeting] {
        meetings.filter { $0.isPast }
    }

    func loadMeetings() async {
        isLoading = true
        error = nil

        do {
            meetings = try await databaseService.fetchAllMeetings()
            print("✅ Loaded \(meetings.count) meetings in ViewModel")
        } catch {
            self.error = error.localizedDescription
            print("❌ Error loading meetings: \(error.localizedDescription)")
        }

        isLoading = false
    }

    func refresh() async {
        await loadMeetings()
    }

    func deleteMeeting(_ meeting: Meeting) async {
        do {
            try await databaseService.deleteMeeting(id: meeting.id)
            await loadMeetings()  // Reload list
        } catch {
            self.error = error.localizedDescription
        }
    }
}
