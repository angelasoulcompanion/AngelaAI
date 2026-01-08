//
//  DateParsingService.swift
//  Angela Brain Dashboard
//
//  Centralized date parsing and formatting service
//  DRY refactor - consolidates 20+ DateFormatter instances
//

import Foundation

/// Centralized date parsing and formatting service
class DateParsingService {
    static let shared = DateParsingService()

    private init() {}

    // MARK: - Cached Formatters (Expensive to create)

    /// ISO8601 formatter for API dates
    private lazy var iso8601Formatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    /// ISO8601 basic (without fractional seconds)
    private lazy var iso8601BasicFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        return formatter
    }()

    // MARK: - Common Date Formats

    /// "yyyy-MM-dd" format (e.g., "2025-01-08")
    private lazy var dateOnlyFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    /// "MMM d, HH:mm" format (e.g., "Jan 8, 14:30")
    lazy var shortDateTimeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMM d, HH:mm"
        return f
    }()

    /// "EEE, MMM d" format (e.g., "Wed, Jan 8")
    lazy var dayDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "EEE, MMM d"
        return f
    }()

    /// "HH:mm" format (e.g., "14:30")
    lazy var timeOnlyFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm"
        return f
    }()

    /// "d MMM yyyy" format (e.g., "8 Jan 2025")
    lazy var mediumDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "d MMM yyyy"
        return f
    }()

    /// "d MMM" format (e.g., "8 Jan")
    lazy var shortDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "d MMM"
        return f
    }()

    /// "EEEE, d MMMM yyyy" format (e.g., "Wednesday, 8 January 2025")
    lazy var fullDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "EEEE, d MMMM yyyy"
        return f
    }()

    /// "E" format for day abbreviations (e.g., "Wed")
    lazy var dayAbbreviationFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "E"
        return f
    }()

    /// Timestamp format for file names (e.g., "20250108_143000")
    lazy var timestampFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyyMMdd_HHmmss"
        return f
    }()

    // MARK: - API Date Parsing (Multiple Formats)

    /// All formatters for API date strings (in order of likelihood)
    private lazy var apiFormatters: [DateFormatter] = {
        let formats = [
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX",   // PostgreSQL with microseconds + timezone
            "yyyy-MM-dd'T'HH:mm:ss.SSSXXX",      // With milliseconds + timezone
            "yyyy-MM-dd'T'HH:mm:ssXXX",          // Without fractional + timezone
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSSZZZZZ", // Alternate timezone format
            "yyyy-MM-dd'T'HH:mm:ss.SSSZZZZZ",
            "yyyy-MM-dd'T'HH:mm:ssZZZZZ",
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",      // Without timezone
            "yyyy-MM-dd'T'HH:mm:ss.SSS",
            "yyyy-MM-dd'T'HH:mm:ss",
            "yyyy-MM-dd"
        ]

        return formats.map { format in
            let f = DateFormatter()
            f.dateFormat = format
            f.locale = Locale(identifier: "en_US_POSIX")
            f.timeZone = TimeZone(secondsFromGMT: 0)
            return f
        }
    }()

    // MARK: - Parsing Methods

    /// Parse date from API string (tries multiple formats)
    func parseAPIDate(_ dateString: String) -> Date {
        // Try ISO8601 first
        if let date = iso8601Formatter.date(from: dateString) {
            return date
        }

        if let date = iso8601BasicFormatter.date(from: dateString) {
            return date
        }

        // Try all formatters
        for formatter in apiFormatters {
            if let date = formatter.date(from: dateString) {
                return date
            }
        }

        // Fallback to current date
        print("⚠️ DateParsingService: Failed to parse date: \(dateString)")
        return Date()
    }

    /// Parse date-only string ("yyyy-MM-dd")
    func parseDateOnly(_ dateString: String) -> Date? {
        return dateOnlyFormatter.date(from: dateString)
    }

    // MARK: - Formatting Methods

    /// Format date as "yyyy-MM-dd"
    func formatDateOnly(_ date: Date) -> String {
        return dateOnlyFormatter.string(from: date)
    }

    /// Format date as "MMM d, HH:mm"
    func formatShortDateTime(_ date: Date) -> String {
        return shortDateTimeFormatter.string(from: date)
    }

    /// Format date as "EEE, MMM d"
    func formatDayDate(_ date: Date) -> String {
        return dayDateFormatter.string(from: date)
    }

    /// Format date as "HH:mm"
    func formatTimeOnly(_ date: Date) -> String {
        return timeOnlyFormatter.string(from: date)
    }

    /// Format date as "d MMM yyyy"
    func formatMediumDate(_ date: Date) -> String {
        return mediumDateFormatter.string(from: date)
    }

    /// Format date as "d MMM"
    func formatShortDate(_ date: Date) -> String {
        return shortDateFormatter.string(from: date)
    }

    /// Format date as "EEEE, d MMMM yyyy"
    func formatFullDate(_ date: Date) -> String {
        return fullDateFormatter.string(from: date)
    }

    /// Format date for file name timestamp
    func formatTimestamp(_ date: Date = Date()) -> String {
        return timestampFormatter.string(from: date)
    }

    // MARK: - Relative Formatting

    /// Returns relative time string (e.g., "2 hours ago", "yesterday")
    func relativeString(from date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .full
        return formatter.localizedString(for: date, relativeTo: Date())
    }

    /// Returns short relative time (e.g., "2h ago")
    func shortRelativeString(from date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - Global Convenience Functions

/// Parse API date string (convenience function)
func parseDate(_ dateString: String) -> Date {
    return DateParsingService.shared.parseAPIDate(dateString)
}

/// Format date as short date time (convenience function)
func formatShortDateTime(_ date: Date) -> String {
    return DateParsingService.shared.formatShortDateTime(date)
}
