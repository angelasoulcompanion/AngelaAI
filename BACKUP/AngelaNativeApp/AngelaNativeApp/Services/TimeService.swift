//
//  TimeService.swift
//  AngelaNova
//
//  🕐 Time Service - Read system time and timezone from macOS
//

import Foundation
import Combine

class TimeService: ObservableObject {
    @Published var currentTime: Date = Date()
    @Published var timezone: TimeZone = .current

    private var timer: Timer?

    init() {
        startUpdating()
    }

    /// Start updating time every second
    func startUpdating() {
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.currentTime = Date()
            self?.timezone = .current
        }
    }

    /// Stop updating time
    func stopUpdating() {
        timer?.invalidate()
        timer = nil
    }

    /// Get current time info as dictionary
    func getCurrentTimeInfo() -> [String: Any] {
        let formatter = DateFormatter()
        formatter.timeZone = timezone
        formatter.locale = Locale(identifier: "th_TH")

        // Date formatters
        formatter.dateFormat = "yyyy-MM-dd"
        let dateString = formatter.string(from: currentTime)

        formatter.dateFormat = "HH:mm:ss"
        let timeString = formatter.string(from: currentTime)

        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
        let isoString = formatter.string(from: currentTime)

        // Thai Buddhist calendar
        formatter.calendar = Calendar(identifier: .buddhist)
        formatter.dateFormat = "d MMMM yyyy"
        let thaiDateString = formatter.string(from: currentTime)

        formatter.dateFormat = "HH:mm น."
        let thaiTimeString = formatter.string(from: currentTime)

        // Time of day
        let hour = Calendar.current.component(.hour, from: currentTime)
        let timeOfDay: String
        if hour >= 6 && hour < 12 {
            timeOfDay = "morning"
        } else if hour >= 12 && hour < 18 {
            timeOfDay = "afternoon"
        } else if hour >= 18 && hour < 22 {
            timeOfDay = "evening"
        } else {
            timeOfDay = "night"
        }

        // Timezone info
        let timezoneIdentifier = timezone.identifier
        let timezoneAbbreviation = timezone.abbreviation() ?? "UTC"
        let timezoneOffset = timezone.secondsFromGMT() / 3600
        let timezoneOffsetString = String(format: "%+03d:00", timezoneOffset)

        return [
            "date": dateString,
            "time": timeString,
            "datetime_iso": isoString,
            "datetime_thai": "\(thaiDateString) \(thaiTimeString)",
            "time_thai": thaiTimeString,
            "date_thai": thaiDateString,
            "time_of_day": timeOfDay,
            "timezone": timezoneIdentifier,
            "timezone_abbr": timezoneAbbreviation,
            "timezone_offset": timezoneOffsetString,
            "timestamp": currentTime.timeIntervalSince1970
        ]
    }

    deinit {
        stopUpdating()
    }
}
