//
//  MeetingListViewModel.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//

import Foundation
import SwiftUI
import Combine

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

    func updateMeetingStatus(meetingId: UUID, newStatus: String) async {
        do {
            try await databaseService.updateMeetingStatus(id: meetingId, status: newStatus)
            print("✅ Updated meeting \(meetingId) to status: \(newStatus)")
        } catch {
            self.error = error.localizedDescription
            print("❌ Error updating meeting status: \(error.localizedDescription)")
        }
    }
}
