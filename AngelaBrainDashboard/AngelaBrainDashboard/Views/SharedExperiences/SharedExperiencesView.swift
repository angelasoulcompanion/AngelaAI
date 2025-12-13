//
//  SharedExperiencesView.swift
//  Angela Brain Dashboard
//
//  💜 Shared Experiences - Beautiful Moments Together 💜
//

import SwiftUI
import Combine

struct SharedExperiencesView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = SharedExperiencesViewModel()
    @State private var searchText = ""

    var body: some View {
        VStack(spacing: 0) {
            // Header with search
            header

            // Experience grid/list
            ScrollView {
                LazyVStack(spacing: AngelaTheme.spacing) {
                    ForEach(filteredExperiences) { experience in
                        ExperienceCard(experience: experience)
                    }
                }
                .padding(AngelaTheme.largeSpacing)
            }
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    private var filteredExperiences: [SharedExperience] {
        if searchText.isEmpty {
            return viewModel.experiences
        }
        return viewModel.experiences.filter {
            ($0.title?.localizedCaseInsensitiveContains(searchText) ?? false) ||
            ($0.description?.localizedCaseInsensitiveContains(searchText) ?? false) ||
            ($0.memorableMoments?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: AngelaTheme.spacing) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Shared Experiences")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("\(viewModel.experiences.count) precious moments together 💜")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()
            }

            // Search bar
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(AngelaTheme.textTertiary)

                TextField("Search experiences...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(12)
            .background(AngelaTheme.backgroundLight)
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }
}

// MARK: - Experience Card Component

struct ExperienceCard: View {
    let experience: SharedExperience
    @EnvironmentObject var databaseService: DatabaseService
    @State private var images: [ExperienceImage] = []

    private var intensityColor: Color {
        Color(hex: experience.intensityColor)
    }

    private var importanceColor: Color {
        Color(hex: experience.importanceColor)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Images Gallery (if available)
            if !images.isEmpty {
                imagesGallery
            }

            // Header: Title + Date + Importance
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    if let title = experience.title {
                        Text(title)
                            .font(AngelaTheme.heading())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .fontWeight(.semibold)
                    }

                    // Place name
                    if let placeName = experience.placeName {
                        HStack(spacing: 4) {
                            Image(systemName: "mappin.circle.fill")
                                .font(.system(size: 10))
                                .foregroundColor(AngelaTheme.primaryPurple)

                            Text(placeName)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.primaryPurple)
                        }
                    }

                    HStack(spacing: 8) {
                        Image(systemName: "calendar")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)

                        Text(experience.experiencedAt, style: .date)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)

                        Text("•")
                            .foregroundColor(AngelaTheme.textTertiary)

                        Text(experience.experiencedAt, style: .relative)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }

                Spacer()

                // Importance stars
                HStack(spacing: 2) {
                    ForEach(Array(0..<10).prefix(min(experience.importanceLevel, 10)), id: \.self) { _ in
                        Image(systemName: "star.fill")
                            .font(.system(size: 10))
                    }
                }
                .foregroundColor(importanceColor)
            }

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            // Description
            if let description = experience.description {
                Text(description)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            // Moods & Emotions
            if experience.davidMood != nil || experience.angelaEmotion != nil {
                HStack(spacing: AngelaTheme.spacing) {
                    if let davidMood = experience.davidMood {
                        MoodTag(
                            icon: "person.fill",
                            label: "David's mood",
                            value: davidMood,
                            color: AngelaTheme.accentGold
                        )
                    }

                    if let angelaEmotion = experience.angelaEmotion {
                        MoodTag(
                            icon: "brain.head.profile",
                            label: "Angela's emotion",
                            value: angelaEmotion,
                            color: AngelaTheme.primaryPurple
                        )
                    }
                }
            }

            // Emotional Intensity Bar
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Emotional Intensity")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    Spacer()

                    Text("\(experience.emotionalIntensity)/10")
                        .font(AngelaTheme.caption())
                        .foregroundColor(intensityColor)
                        .fontWeight(.semibold)
                }

                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        // Background
                        RoundedRectangle(cornerRadius: 4)
                            .fill(AngelaTheme.backgroundLight)
                            .frame(height: 8)

                        // Progress
                        RoundedRectangle(cornerRadius: 4)
                            .fill(
                                LinearGradient(
                                    colors: [intensityColor.opacity(0.7), intensityColor],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: geometry.size.width * CGFloat(experience.emotionalIntensity) / 10.0, height: 8)
                    }
                }
                .frame(height: 8)
            }

            // Memorable Moments
            if let moments = experience.memorableMoments {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: "sparkles")
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.accentGold)

                        Text("Memorable Moments")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .fontWeight(.semibold)
                    }

                    Text(moments)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .italic()
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .background(AngelaTheme.accentGold.opacity(0.1))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }

            // What Angela Learned
            if let learned = experience.whatAngelaLearned {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: "brain.head.profile")
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.primaryPurple)

                        Text("What Angela Learned")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .fontWeight(.semibold)
                    }

                    Text(learned)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .background(AngelaTheme.primaryPurple.opacity(0.1))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(
            LinearGradient(
                colors: [intensityColor.opacity(0.05), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(intensityColor.opacity(0.3), lineWidth: 1)
        )
        .task {
            await loadImages()
        }
    }

    // MARK: - Images Gallery

    private var imagesGallery: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(images) { image in
                    ExperienceImageView(image: image)
                }
            }
        }
        .frame(height: 200)
    }

    // MARK: - Load Images

    private func loadImages() async {
        do {
            images = try await databaseService.fetchExperienceImages(experienceId: experience.id)
        } catch {
            print("Error loading images for experience \(experience.id): \(error)")
        }
    }
}

// MARK: - Experience Image View

struct ExperienceImageView: View {
    let image: ExperienceImage

    private var nsImage: NSImage? {
        guard !image.imageData.isEmpty else { return nil }

        // Create NSImage with orientation handled
        guard let cgImage = createCGImage(from: image.imageData) else {
            // Fallback to standard NSImage
            return NSImage(data: image.imageData)
        }

        let nsImage = NSImage(cgImage: cgImage, size: NSSize(width: cgImage.width, height: cgImage.height))
        return nsImage
    }

    // Helper to create CGImage with proper orientation
    private func createCGImage(from data: Data) -> CGImage? {
        guard let imageSource = CGImageSourceCreateWithData(data as CFData, nil),
              let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
            return nil
        }

        // Get EXIF orientation
        let properties = CGImageSourceCopyPropertiesAtIndex(imageSource, 0, nil) as? [String: Any]
        let orientationValue = properties?[kCGImagePropertyOrientation as String] as? UInt32 ?? 1

        // Debug: Print orientation value
        print("🔍 Image orientation value: \(orientationValue)")

        // If orientation is 1 (normal), return as-is
        if orientationValue == 1 {
            print("⚠️ Orientation is 1 (normal), but image appears sideways - forcing rotation")
            // Image appears sideways, so let's rotate it 90° CCW (orientation 8)
            // return cgImage
        }

        // Create context for rotation
        let width = cgImage.width
        let height = cgImage.height

        var transform = CGAffineTransform.identity
        var outputSize = CGSize(width: width, height: height)

        // Apply transformation based on EXIF orientation
        // If orientation is 1 but image is landscape, force rotation
        let actualOrientation: UInt32
        if orientationValue == 1 && width > height {
            // Landscape image that should be portrait - rotate 90° CCW
            actualOrientation = 8
            print("🔄 Forcing rotation: Landscape → Portrait (90° CCW)")
        } else {
            actualOrientation = orientationValue
        }

        switch actualOrientation {
        case 3: // 180° rotation
            transform = transform.translatedBy(x: CGFloat(width), y: CGFloat(height))
            transform = transform.rotated(by: .pi)
            print("🔄 Applying 180° rotation")
        case 6: // 90° CW
            outputSize = CGSize(width: height, height: width)
            transform = transform.translatedBy(x: CGFloat(height), y: 0)
            transform = transform.rotated(by: .pi / 2)
            print("🔄 Applying 90° CW rotation")
        case 8: // 90° CCW
            outputSize = CGSize(width: height, height: width)
            transform = transform.translatedBy(x: 0, y: CGFloat(width))
            transform = transform.rotated(by: -.pi / 2)
            print("🔄 Applying 90° CCW rotation")
        default:
            print("⚠️ No rotation applied, returning original")
            return cgImage
        }

        // Create bitmap context
        guard let colorSpace = cgImage.colorSpace,
              let context = CGContext(data: nil,
                                     width: Int(outputSize.width),
                                     height: Int(outputSize.height),
                                     bitsPerComponent: cgImage.bitsPerComponent,
                                     bytesPerRow: 0,
                                     space: colorSpace,
                                     bitmapInfo: cgImage.bitmapInfo.rawValue) else {
            return cgImage
        }

        context.concatenate(transform)
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

        return context.makeImage()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Image
            if let nsImage = nsImage {
                Image(nsImage: nsImage)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 180, height: 160)
                    .cornerRadius(8)
                    .clipped()
            } else {
                // Placeholder if image failed to load
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(width: 180, height: 160)

                    VStack(spacing: 8) {
                        Image(systemName: "photo")
                            .font(.system(size: 40))
                            .foregroundColor(AngelaTheme.textTertiary)

                        Text("No Image")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }
            }

            // Caption (only show if not empty and not "nil")
            if let caption = image.imageCaption, !caption.isEmpty, caption.lowercased() != "nil" {
                Text(caption)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(2)
                    .frame(width: 180)
            }

            // Angela's observation (only show if not empty and not "nil")
            if let observation = image.angelaObservation, !observation.isEmpty, observation.lowercased() != "nil" {
                HStack(spacing: 4) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text(observation)
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .lineLimit(2)
                }
                .frame(width: 180)
            }
        }
    }
}

// MARK: - Mood Tag Component

struct MoodTag: View {
    let icon: String
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 10))
                .foregroundColor(color)

            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.system(size: 9))
                    .foregroundColor(AngelaTheme.textTertiary)

                Text(value)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(color)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color.opacity(0.15))
        .cornerRadius(8)
    }
}

// MARK: - View Model

@MainActor
class SharedExperiencesViewModel: ObservableObject {
    @Published var experiences: [SharedExperience] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            experiences = try await databaseService.fetchSharedExperiences(limit: 50)
        } catch {
            print("Error loading shared experiences: \(error)")
        }

        isLoading = false
    }
}
