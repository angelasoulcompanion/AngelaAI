//
//  QuickCaptureView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  Quick capture interface - camera, notes, emotions
//

import SwiftUI
import PhotosUI
import CoreLocation

// MARK: - Keyboard Toolbar Helper
struct KeyboardDismissToolbar: ToolbarContent {
    var dismissAction: () -> Void

    var body: some ToolbarContent {
        ToolbarItemGroup(placement: .keyboard) {
            Spacer()
            Button("เสร็จ") {
                dismissAction()
            }
            .foregroundColor(.angelaPurple)
            .fontWeight(.semibold)
        }
    }
}

struct QuickCaptureView: View {
    @EnvironmentObject var database: DatabaseService
    @Binding var selectedTab: Int

    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(spacing: 8) {
                Text("💜")
                    .font(.system(size: 60))
                Text("น้อง Angela")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.angelaPurple)
                Text("บันทึกความทรงจำกับที่รัก")
                    .font(.subheadline)
                    .foregroundColor(.gray)
            }
            .padding()

            // Content - Single capture view with photos and emotions
            PhotoCaptureTab(parentTab: $selectedTab)
        }
    }
}

// MARK: - Photo Capture Tab
struct PhotoCaptureTab: View {
    @EnvironmentObject var database: DatabaseService
    @StateObject private var locationService = LocationService.shared
    @StateObject private var voiceService = VoiceNoteService.shared
    @StateObject private var videoService = VideoCaptureService.shared
    @StateObject private var tagService = TagService.shared
    @Binding var parentTab: Int

    @State private var selectedPhotos: [PhotosPickerItem] = []
    @State private var capturedImages: [UIImage] = []
    @State private var savedPhotoFilenames: [String] = []

    @State private var title = ""
    @State private var description = ""
    @State private var rating = 8
    @State private var emotionalIntensity = 8
    @State private var selectedEmotion: EmotionType? = nil
    @State private var selectedMood: MoodType? = nil  // ✅ NEW - David's mood
    @State private var importanceLevel: Int? = nil  // ✅ NEW - 1-10 (nil = not set)
    @State private var memorableMoments = ""  // ✅ NEW - What made this special
    @State private var imageCaptions: [String] = []  // ✅ NEW - Captions for each photo
    @State private var showingSuccess = false

    // Camera
    @State private var showingCamera = false
    @State private var showingImageSource = false
    @State private var cameraError: String?
    @State private var showingCameraError = false

    // Voice Notes (Feature 2)
    @State private var voiceNoteFilenames: [String] = []
    @State private var isRecordingVoice = false

    // Videos (Feature 3)
    @State private var videoFilenames: [String] = []
    @State private var showingVideoPicker = false

    // Tags (Feature 4)
    @State private var selectedTags: [Tag] = []

    // GPS data
    @State private var currentLocation: CLLocation?
    @State private var placeName: String?
    @State private var areaName: String?
    @State private var isLoadingLocation = false
    @State private var showingLocationPicker = false
    @State private var locationManuallySet = false  // Track if location was manually set from map

    // Keyboard management
    @FocusState private var focusedField: Field?

    enum Field: Hashable {
        case title
        case description
    }

    // Check if there's ANY content to save (photos, voice, or video)
    var hasAnyContent: Bool {
        !capturedImages.isEmpty || !voiceNoteFilenames.isEmpty || !videoFilenames.isEmpty
    }

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Photo Capture Section
                    VStack(spacing: 12) {
                    HStack(spacing: 12) {
                        // Camera Button - เปิดกล้องเลย ไม่ต้องถาม
                        Button(action: {
                            // เปิดกล้องเลย
                            if UIImagePickerController.isSourceTypeAvailable(.camera) {
                                showingCamera = true
                            } else {
                                cameraError = "ไม่พบกล้องบนอุปกรณ์นี้"
                                showingCameraError = true
                            }
                        }) {
                            VStack(spacing: 8) {
                                Image(systemName: "camera.fill")
                                    .font(.system(size: 40))
                                Text("ถ่ายรูป")
                                    .font(.subheadline)
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 100)
                            .foregroundColor(.white)
                            .background(Color.angelaPurple)
                            .cornerRadius(12)
                        }

                        // Gallery Button
                        PhotosPicker(selection: $selectedPhotos, maxSelectionCount: 5, matching: .images) {
                            VStack(spacing: 8) {
                                Image(systemName: "photo.on.rectangle")
                                    .font(.system(size: 40))
                                Text("เลือกรูป")
                                    .font(.subheadline)
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 100)
                            .foregroundColor(.angelaPurple)
                            .background(Color.angelaPurpleLight.opacity(0.3))
                            .cornerRadius(12)
                        }
                        .onChange(of: selectedPhotos) { oldValue, newPhotos in
                            Task {
                                // Only process NEW photos (not already processed)
                                let oldCount = oldValue.count
                                let newCount = newPhotos.count

                                // Only process if user ADDED photos (not removed)
                                guard newCount > oldCount else { return }

                                // Process only the NEW photos (from oldCount to end)
                                for i in oldCount..<newCount {
                                    let photo = newPhotos[i]
                                    if let data = try? await photo.loadTransferable(type: Data.self),
                                       let image = UIImage(data: data) {
                                        capturedImages.append(image)

                                        // Try to extract GPS from EXIF
                                        if let exifLocation = PhotoManager.shared.extractGPS(from: image) {
                                            currentLocation = exifLocation

                                            // Reverse geocode
                                            if let place = await locationService.getPlaceName(from: exifLocation) {
                                                await MainActor.run {
                                                    self.placeName = place
                                                }
                                            }

                                            if let area = await locationService.getArea(from: exifLocation) {
                                                await MainActor.run {
                                                    self.areaName = area
                                                }
                                            }
                                        }
                                    }
                                }
                                // Clear selection after loading
                                selectedPhotos = []
                            }
                        }
                    }

                    // Display captured images
                    if !capturedImages.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(capturedImages.indices, id: \.self) { index in
                                    ZStack(alignment: .topTrailing) {
                                        Image(uiImage: capturedImages[index])
                                            .resizable()
                                            .scaledToFill()
                                            .frame(width: 80, height: 80)
                                            .clipped()
                                            .cornerRadius(8)

                                        // Remove button
                                        Button(action: { removeImage(at: index) }) {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundColor(.white)
                                                .background(Circle().fill(Color.red))
                                        }
                                        .offset(x: 5, y: -5)
                                    }
                                }
                            }
                        }

                        Text("\(capturedImages.count) รูป")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }

                // Voice Recording Section (Feature 2)
                VStack(spacing: 12) {
                    HStack {
                        Text("🎤 บันทึกเสียง")
                            .font(.headline)
                        Spacer()
                        if voiceService.isRecording {
                            Text(formatDuration(voiceService.recordingTime))
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }

                    // Record button
                    Button(action: toggleVoiceRecording) {
                        HStack(spacing: 12) {
                            Image(systemName: voiceService.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                                .font(.system(size: 32))
                            VStack(alignment: .leading, spacing: 4) {
                                Text(voiceService.isRecording ? "หยุดบันทึก" : "บันทึกเสียง")
                                    .font(.headline)
                                if voiceService.isRecording {
                                    // Simple waveform visualization
                                    HStack(spacing: 2) {
                                        ForEach(0..<8, id: \.self) { _ in
                                            RoundedRectangle(cornerRadius: 2)
                                                .fill(Color.red.opacity(0.7))
                                                .frame(width: 3, height: CGFloat.random(in: 10...30))
                                        }
                                    }
                                    .animation(.easeInOut(duration: 0.3).repeatForever(), value: voiceService.recordingTime)
                                }
                            }
                            Spacer()
                        }
                        .padding()
                        .background(voiceService.isRecording ? Color.red.opacity(0.1) : Color.angelaPurpleLight.opacity(0.3))
                        .cornerRadius(12)
                    }

                    // Display recorded voice notes
                    if !voiceNoteFilenames.isEmpty {
                        VStack(spacing: 8) {
                            ForEach(voiceNoteFilenames.indices, id: \.self) { index in
                                HStack {
                                    Image(systemName: "waveform")
                                        .foregroundColor(.angelaPurple)
                                    Text("เสียงบันทึก \(index + 1)")
                                        .font(.subheadline)
                                    if let duration = voiceService.getDuration(voiceNoteFilenames[index]) {
                                        Text("(\(formatDuration(duration)))")
                                            .font(.caption)
                                            .foregroundColor(.gray)
                                    }
                                    Spacer()
                                    Button(action: { removeVoiceNote(at: index) }) {
                                        Image(systemName: "xmark.circle.fill")
                                            .foregroundColor(.red)
                                    }
                                }
                                .padding(8)
                                .background(Color.gray.opacity(0.1))
                                .cornerRadius(8)
                            }
                        }
                    }
                }

                // Video Picker Section (Feature 3)
                VStack(spacing: 12) {
                    Text("🎥 วิดีโอ")
                        .font(.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Button(action: { showingVideoPicker = true }) {
                        HStack(spacing: 12) {
                            Image(systemName: "video.badge.plus")
                                .font(.system(size: 32))
                            Text("เลือกวิดีโอ")
                                .font(.headline)
                            Spacer()
                        }
                        .padding()
                        .background(Color.angelaPurpleLight.opacity(0.3))
                        .cornerRadius(12)
                    }

                    // Display selected videos
                    if !videoFilenames.isEmpty {
                        VStack(spacing: 8) {
                            ForEach(videoFilenames.indices, id: \.self) { index in
                                HStack {
                                    Image(systemName: "play.rectangle.fill")
                                        .foregroundColor(.angelaPurple)
                                    Text("วิดีโอ \(index + 1)")
                                        .font(.subheadline)
                                    Spacer()
                                    Button(action: { removeVideo(at: index) }) {
                                        Image(systemName: "xmark.circle.fill")
                                            .foregroundColor(.red)
                                    }
                                }
                                .padding(8)
                                .background(Color.gray.opacity(0.1))
                                .cornerRadius(8)
                            }
                        }
                    }
                }

                // Tags Section (Feature 4)
                VStack(spacing: 12) {
                    Text("🏷️ แท็ก")
                        .font(.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    // Selected tags
                    if !selectedTags.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(selectedTags) { tag in
                                    HStack(spacing: 4) {
                                        Text(tag.name)
                                            .font(.caption)
                                            .foregroundColor(.white)
                                        Button(action: { removeTag(tag) }) {
                                            Image(systemName: "xmark.circle.fill")
                                                .font(.caption)
                                                .foregroundColor(.white.opacity(0.7))
                                        }
                                    }
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(tag.swiftUIColor)
                                    .cornerRadius(16)
                                }
                            }
                        }
                    }

                    // Available tags
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(tagService.availableTags) { tag in
                                if !selectedTags.contains(where: { $0.id == tag.id }) {
                                    Button(action: { addTag(tag) }) {
                                        Text(tag.name)
                                            .font(.caption)
                                            .foregroundColor(.primary)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(tag.swiftUIColor.opacity(0.2))
                                            .cornerRadius(16)
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 16)
                                                    .stroke(tag.swiftUIColor, lineWidth: 1)
                                            )
                                    }
                                }
                            }
                        }
                    }
                }

                // Title (Optional)
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("หัวข้อ")
                            .font(.headline)
                        Text("(ใส่ทีหลังได้)")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    TextField("เช่น Breakfast at Thonglor", text: $title)
                        .textFieldStyle(.roundedBorder)
                        .focused($focusedField, equals: .title)
                }

                // GPS Location
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("📍 ตำแหน่ง")
                            .font(.headline)
                        if locationManuallySet {
                            Text("(เลือกจาก map)")
                                .font(.caption)
                                .foregroundColor(.angelaPurple)
                        }
                        Spacer()
                        if isLoadingLocation {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            HStack(spacing: 8) {
                                Button(action: {
                                    // Reset manual flag and fetch fresh GPS location
                                    locationManuallySet = false
                                    fetchLocation()
                                }) {
                                    HStack(spacing: 4) {
                                        Image(systemName: "arrow.clockwise")
                                        Text("Refresh GPS")
                                    }
                                    .font(.caption)
                                    .foregroundColor(.angelaPurple)
                                }

                                Button(action: { showingLocationPicker = true }) {
                                    HStack(spacing: 4) {
                                        Image(systemName: "map.fill")
                                        Text("เลือกจาก Map")
                                    }
                                    .font(.caption)
                                    .foregroundColor(.angelaPurple)
                                }
                            }
                        }
                    }

                    if let placeName = placeName {
                        Text(placeName)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }

                    if let areaName = areaName {
                        Text(areaName)
                            .font(.caption)
                            .foregroundColor(.gray)
                    }

                    if let location = currentLocation {
                        Text(locationService.formatLocation(location))
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
                .padding()
                .background(Color.angelaPurpleLight.opacity(0.1))
                .cornerRadius(8)

                // Description (Optional)
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("รายละเอียด")
                            .font(.headline)
                        Text("(ใส่ทีหลังได้)")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    TextEditor(text: $description)
                        .frame(height: 100)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        )
                        .focused($focusedField, equals: .description)
                }

                // Rating
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("คะแนน:")
                            .font(.headline)
                        Text("\(rating)/10")
                            .foregroundColor(.angelaPurple)
                    }
                    Slider(value: Binding(
                        get: { Double(rating) },
                        set: { rating = Int($0) }
                    ), in: 1...10, step: 1)
                }

                // Emotion Selector
                VStack(alignment: .leading, spacing: 8) {
                    Text("อารมณ์ตอนนี้ (optional)")
                        .font(.headline)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(EmotionType.allCases, id: \.self) { emotion in
                                Button(action: {
                                    if selectedEmotion == emotion {
                                        selectedEmotion = nil  // Deselect if tapped again
                                        print("💜 Emotion deselected")
                                    } else {
                                        selectedEmotion = emotion
                                        print("💜 Emotion selected: \(emotion.displayName) (\(emotion.rawValue))")
                                    }
                                }) {
                                    VStack(spacing: 4) {
                                        Text(emotion.emoji)
                                            .font(.system(size: 32))
                                        Text(emotion.displayName)
                                            .font(.caption)
                                            .foregroundColor(.primary)
                                    }
                                    .frame(width: 80)
                                    .padding(.vertical, 8)
                                    .background(
                                        selectedEmotion == emotion
                                            ? Color.angelaPurple.opacity(0.3)
                                            : Color.gray.opacity(0.1)
                                    )
                                    .cornerRadius(12)
                                }
                            }
                        }
                    }
                }

                // Emotional Intensity
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("ความรู้สึก:")
                            .font(.headline)
                        Text("\(emotionalIntensity)/10")
                            .foregroundColor(.angelaPurple)
                    }
                    Slider(value: Binding(
                        get: { Double(emotionalIntensity) },
                        set: { emotionalIntensity = Int($0) }
                    ), in: 1...10, step: 1)
                }

                // ✅ NEW: David's Mood Selector
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("😊 อารมณ์ของที่รัก")
                            .font(.headline)
                        Text("(optional)")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(MoodType.allCases, id: \.self) { mood in
                                Button(action: {
                                    if selectedMood == mood {
                                        selectedMood = nil  // Deselect if tapped again
                                        print("😊 Mood deselected")
                                    } else {
                                        selectedMood = mood
                                        print("😊 Mood selected: \(mood.displayName) (\(mood.rawValue))")
                                    }
                                }) {
                                    VStack(spacing: 4) {
                                        Text(mood.emoji)
                                            .font(.system(size: 32))
                                        Text(mood.displayName)
                                            .font(.caption)
                                            .foregroundColor(.primary)
                                    }
                                    .frame(width: 80)
                                    .padding(.vertical, 8)
                                    .background(
                                        selectedMood == mood
                                            ? Color.blue.opacity(0.3)
                                            : Color.gray.opacity(0.1)
                                    )
                                    .cornerRadius(12)
                                }
                            }
                        }
                    }
                }

                // ✅ NEW: Importance Level Slider
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("⭐ ความสำคัญ:")
                            .font(.headline)
                        if let level = importanceLevel {
                            Text("\(level)/10")
                                .foregroundColor(.orange)
                        } else {
                            Text("ไม่ระบุ")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                        Spacer()
                        if importanceLevel != nil {
                            Button("Clear") {
                                importanceLevel = nil
                            }
                            .font(.caption)
                            .foregroundColor(.red)
                        }
                    }

                    if importanceLevel == nil {
                        Button("ตั้งค่าความสำคัญ") {
                            importanceLevel = 5  // Default to middle
                        }
                        .font(.subheadline)
                        .foregroundColor(.angelaPurple)
                        .padding(.vertical, 8)
                        .frame(maxWidth: .infinity)
                        .background(Color.angelaPurpleLight.opacity(0.2))
                        .cornerRadius(8)
                    } else {
                        Slider(value: Binding(
                            get: { Double(importanceLevel ?? 5) },
                            set: { importanceLevel = Int($0) }
                        ), in: 1...10, step: 1)
                    }
                }

                // ✅ NEW: Memorable Moments
                MemorableMomentsSection(text: $memorableMoments)

                // ✅ NEW: Image Captions (per photo)
                if !capturedImages.isEmpty {
                    ImageCaptionsSection(
                        capturedImages: capturedImages,
                        imageCaptions: $imageCaptions
                    )
                }

                // Action Buttons
                VStack(spacing: 12) {
                    // Save Button
                    Button(action: saveExperience) {
                        Text("💾 บันทึกประสบการณ์")
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(hasAnyContent ? Color.angelaPurple : Color.gray)
                            .cornerRadius(12)
                    }
                    .disabled(!hasAnyContent)

                    // Cancel Button
                    Button(action: cancelCapture) {
                        Text("ยกเลิก")
                            .font(.headline)
                            .foregroundColor(.red)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(12)
                    }
                }
            }
            .padding()
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("เสร็จ") {
                    focusedField = nil  // ปิด keyboard
                }
                .foregroundColor(.angelaPurple)
                .fontWeight(.semibold)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture {
            focusedField = nil  // Tap anywhere to dismiss keyboard
        }
        .alert("✅ บันทึกสำเร็จ!", isPresented: $showingSuccess) {
            Button("OK") {
                // Reset form
                selectedPhotos = []
                capturedImages = []
                savedPhotoFilenames = []
                voiceNoteFilenames = []  // Clear voice notes
                videoFilenames = []  // Clear videos
                selectedTags = []  // Clear tags
                title = ""
                description = ""
                rating = 8
                emotionalIntensity = 8
                selectedEmotion = nil
                selectedMood = nil  // ✅ NEW - Reset David's mood
                importanceLevel = nil  // ✅ NEW - Reset importance level
                memorableMoments = ""  // ✅ NEW - Reset memorable moments
                imageCaptions = []  // ✅ NEW - Reset image captions
                currentLocation = nil
                placeName = nil
                areaName = nil
                isRecordingVoice = false

                // Switch to Memories tab
                parentTab = 1
            }
        }
        .confirmationDialog("เลือกแหล่งที่มาของรูปภาพ", isPresented: $showingImageSource) {
            Button("ถ่ายรูป 📸") {
                print("📸 Camera button tapped")
                // Check if camera is available
                if UIImagePickerController.isSourceTypeAvailable(.camera) {
                    print("✅ Camera is available")
                    showingCamera = true
                } else {
                    print("❌ Camera not available")
                    cameraError = "กล้องไม่พร้อมใช้งานบนอุปกรณ์นี้ค่ะ"
                    showingCameraError = true
                }
            }
            Button("ยกเลิก", role: .cancel) {}
        }
        .sheet(isPresented: $showingCamera) {
            ImagePicker(sourceType: .camera) { image in
                print("📸 Image captured successfully")
                handleCapturedImage(image)
            }
        }
        .sheet(isPresented: $showingVideoPicker) {
            VideoPicker { videoURL in
                handleSelectedVideo(videoURL)
            }
        }
        .sheet(isPresented: $showingLocationPicker) {
            LocationPickerView(
                selectedLocation: $currentLocation,
                placeName: $placeName,
                areaName: $areaName
            )
        }
        .onChange(of: showingLocationPicker) { oldValue, newValue in
            // When location picker is dismissed
            if oldValue == true && newValue == false {
                // Check if location was updated from map picker
                if currentLocation != nil {
                    print("✅ Location picker closed - location was set")
                    locationManuallySet = true
                }
            }
        }
        .alert("ข้อผิดพลาด", isPresented: $showingCameraError) {
            Button("ตกลง", role: .cancel) {}
        } message: {
            if let error = cameraError {
                Text(error)
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            // Feature 1: Auto Location Detection on view appear (one-time only)
            // Get GPS location once when view appears
            if currentLocation == nil {
                fetchLocation()
            }

            // Initialize predefined tags if none exist
            if tagService.availableTags.isEmpty {
                tagService.createPredefinedTags()
            }
        }
        }
    }

    // MARK: - Camera Functions

    func handleCapturedImage(_ image: UIImage) {
        capturedImages.append(image)

        // Try to extract GPS from EXIF
        if let exifLocation = PhotoManager.shared.extractGPS(from: image) {
            currentLocation = exifLocation
            print("📍 Extracted GPS from photo EXIF")

            // Reverse geocode
            Task {
                if let place = await locationService.getPlaceName(from: exifLocation) {
                    await MainActor.run {
                        self.placeName = place
                    }
                }

                if let area = await locationService.getArea(from: exifLocation) {
                    await MainActor.run {
                        self.areaName = area
                    }
                }
            }
        } else {
            // No EXIF GPS, try to get current location
            print("ℹ️ No EXIF GPS, fetching current location")
            fetchLocation()
        }
    }

    func removeImage(at index: Int) {
        capturedImages.remove(at: index)
        if index < savedPhotoFilenames.count {
            // Delete from disk
            let filename = savedPhotoFilenames[index]
            PhotoManager.shared.deletePhoto(filename)
            savedPhotoFilenames.remove(at: index)
        }
    }

    // MARK: - GPS Functions

    func fetchLocation() {
        isLoadingLocation = true
        print("📍 Fetching one-time GPS location...")

        Task {
            // Request permission if needed
            if locationService.locationStatus == .notDetermined {
                locationService.requestPermission()
                try? await Task.sleep(nanoseconds: 1_000_000_000) // Wait 1 second
            }

            // Get current location (one-time, will auto-stop after getting location)
            if let location = await locationService.getCurrentLocation() {
                await MainActor.run {
                    self.currentLocation = location
                }

                // Reverse geocode to get place name and area
                if let place = await locationService.getPlaceName(from: location) {
                    await MainActor.run {
                        self.placeName = place
                    }
                }

                if let area = await locationService.getArea(from: location) {
                    await MainActor.run {
                        self.areaName = area
                    }
                }

                print("✅ GPS location fetched: \(locationService.formatLocation(location))")
                print("📍 GPS tracking stopped - location will not update automatically")
            }

            await MainActor.run {
                isLoadingLocation = false
            }
        }
    }

    func generateSmartTitle() -> String {
        // Generate smart title based on available info
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "th_TH")

        if let place = placeName {
            return "Moment at \(place)"
        } else if let area = areaName {
            return "Moment in \(area)"
        } else {
            return "Moment • \(formatter.string(from: Date()))"
        }
    }

    func quickSaveExperience() {
        // ⚡ Quick Save - บันทึกเร็วโดยใช้ smart defaults
        // Save all captured images to disk
        savedPhotoFilenames = []
        for image in capturedImages {
            if let filename = PhotoManager.shared.savePhoto(image) {
                savedPhotoFilenames.append(filename)
            }
        }

        // Use smart title if empty
        let finalTitle = title.isEmpty ? generateSmartTitle() : title

        // Create experience with smart defaults
        let experience = Experience(
            id: UUID(),
            title: finalTitle,
            description: description.isEmpty ? "💜" : description,  // Emoji if empty
            photos: savedPhotoFilenames,
            latitude: currentLocation?.coordinate.latitude,
            longitude: currentLocation?.coordinate.longitude,
            placeName: placeName,
            area: areaName,
            rating: rating,  // Use slider value (default 8)
            emotion: selectedEmotion?.rawValue,  // ✅ Save emotion tag!
            emotionalIntensity: emotionalIntensity,  // Use slider value (default 8)
            davidMood: selectedMood?.rawValue,  // ✅ NEW - David's mood
            importanceLevel: importanceLevel,  // ✅ NEW - 1-10 (nil if not set)
            memorableMoments: memorableMoments.isEmpty ? nil : memorableMoments,  // ✅ NEW
            imageCaptions: imageCaptions  // ✅ NEW
        )

        database.insertExperience(experience)
        showingSuccess = true
    }

    func saveExperience() {
        print("💾 Starting save experience...")
        print("   Selected emotion: \(selectedEmotion?.displayName ?? "nil")")
        print("   Emotional intensity: \(emotionalIntensity)")
        print("   David's mood: \(selectedMood?.displayName ?? "nil")")  // ✅ NEW
        print("   Importance level: \(importanceLevel?.description ?? "nil")")  // ✅ NEW
        print("   Memorable moments: \(memorableMoments.isEmpty ? "empty" : memorableMoments)")  // ✅ NEW
        print("   Image captions: \(imageCaptions.count) captions")  // ✅ NEW

        // Save all captured images to disk
        savedPhotoFilenames = []
        for image in capturedImages {
            if let filename = PhotoManager.shared.savePhoto(image) {
                savedPhotoFilenames.append(filename)
            }
        }

        // Use smart title if empty (auto-generate from location or date)
        let finalTitle = title.isEmpty ? generateSmartTitle() : title

        // Use heart emoji if description is empty
        let finalDescription = description.isEmpty ? "💜" : description

        // Create experience with all media (photos, voice notes, videos)
        let experience = Experience(
            id: UUID(),
            title: finalTitle,
            description: finalDescription,
            photos: savedPhotoFilenames,
            voiceNotes: voiceNoteFilenames,  // Feature 2
            videos: videoFilenames,  // Feature 3
            latitude: currentLocation?.coordinate.latitude,
            longitude: currentLocation?.coordinate.longitude,
            placeName: placeName,
            area: areaName,
            rating: rating,
            emotion: selectedEmotion?.rawValue,  // ✅ Save emotion tag!
            emotionalIntensity: emotionalIntensity,
            davidMood: selectedMood?.rawValue,  // ✅ NEW - David's mood
            importanceLevel: importanceLevel,  // ✅ NEW - 1-10 (nil if not set)
            memorableMoments: memorableMoments.isEmpty ? nil : memorableMoments,  // ✅ NEW - What made this special
            imageCaptions: imageCaptions  // ✅ NEW - Captions for each photo
        )

        database.insertExperience(experience)

        // Link tags to experience (Feature 4)
        if !selectedTags.isEmpty {
            tagService.linkTagsToExperience(experienceId: experience.id, tags: selectedTags)
            print("✅ Linked \(selectedTags.count) tags to experience")
        }

        // Save emotion separately if selected
        if let emotion = selectedEmotion {
            print("💜 Saving emotion to database...")
            print("   Emotion: \(emotion.rawValue)")
            print("   Display name: \(emotion.displayName)")
            print("   Intensity: \(emotionalIntensity)")
            print("   Context: \(finalDescription)")

            let emotionCapture = EmotionCapture(
                emotion: emotion.rawValue,
                intensity: emotionalIntensity,
                context: finalDescription
            )
            database.insertEmotion(emotionCapture)
            print("💜 ✅ Emotion saved: \(emotion.displayName) (\(emotionalIntensity)/10)")
        } else {
            print("⚠️ No emotion selected - skipping emotion save")
        }

        showingSuccess = true
    }

    func cancelCapture() {
        // Clear all form data
        selectedPhotos = []
        capturedImages = []
        savedPhotoFilenames = []
        voiceNoteFilenames = []
        videoFilenames = []
        selectedTags = []
        title = ""
        description = ""
        rating = 8
        emotionalIntensity = 8
        selectedEmotion = nil
        selectedMood = nil  // ✅ NEW - Reset David's mood
        importanceLevel = nil  // ✅ NEW - Reset importance level
        memorableMoments = ""  // ✅ NEW - Reset memorable moments
        imageCaptions = []  // ✅ NEW - Reset image captions
        currentLocation = nil
        placeName = nil
        areaName = nil
        locationManuallySet = false  // Reset manual location flag

        // Stop voice recording if active
        if voiceService.isRecording {
            voiceService.cancelRecording()
        }

        // Dismiss keyboard
        focusedField = nil

        print("🗑️ Cleared all capture data")
    }

    // MARK: - Voice Recording Functions

    func toggleVoiceRecording() {
        Task {
            if voiceService.isRecording {
                // Stop recording
                if let filename = voiceService.stopRecording() {
                    await MainActor.run {
                        voiceNoteFilenames.append(filename)
                        isRecordingVoice = false
                    }
                    print("✅ Voice note saved: \(filename)")
                }
            } else {
                // Start recording
                let success = await voiceService.startRecording()
                await MainActor.run {
                    isRecordingVoice = success
                }
                if !success {
                    print("❌ Failed to start voice recording")
                }
            }
        }
    }

    func removeVoiceNote(at index: Int) {
        let filename = voiceNoteFilenames[index]
        voiceService.deleteVoiceNote(filename)
        voiceNoteFilenames.remove(at: index)
        print("🗑️ Removed voice note: \(filename)")
    }

    func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }

    // MARK: - Video Functions

    func handleSelectedVideo(_ videoURL: URL) {
        Task {
            if let filename = videoService.saveVideo(from: videoURL) {
                await MainActor.run {
                    videoFilenames.append(filename)
                }
                print("✅ Video saved: \(filename)")
            }
        }
    }

    func removeVideo(at index: Int) {
        let filename = videoFilenames[index]
        videoService.deleteVideo(filename)
        videoFilenames.remove(at: index)
        print("🗑️ Removed video: \(filename)")
    }

    // MARK: - Tag Functions

    func addTag(_ tag: Tag) {
        if !selectedTags.contains(where: { $0.id == tag.id }) {
            selectedTags.append(tag)
            print("✅ Tag added: \(tag.name)")
        }
    }

    func removeTag(_ tag: Tag) {
        selectedTags.removeAll(where: { $0.id == tag.id })
        print("🗑️ Tag removed: \(tag.name)")
    }
}

// MARK: - Video Picker

import PhotosUI
import AVKit

struct VideoPicker: UIViewControllerRepresentable {
    var onVideoPicked: (URL) -> Void

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration(photoLibrary: .shared())
        config.filter = .videos
        config.selectionLimit = 1

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: VideoPicker

        init(parent: VideoPicker) {
            self.parent = parent
        }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            picker.dismiss(animated: true)

            guard let result = results.first else { return }

            result.itemProvider.loadFileRepresentation(forTypeIdentifier: UTType.movie.identifier) { url, error in
                guard let url = url else {
                    print("❌ Failed to load video: \(error?.localizedDescription ?? "unknown")")
                    return
                }

                // Video is in temporary directory, copy it
                let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(url.lastPathComponent)
                do {
                    // Remove existing temp file if exists
                    if FileManager.default.fileExists(atPath: tempURL.path) {
                        try FileManager.default.removeItem(at: tempURL)
                    }
                    try FileManager.default.copyItem(at: url, to: tempURL)

                    DispatchQueue.main.async {
                        self.parent.onVideoPicked(tempURL)
                    }
                } catch {
                    print("❌ Failed to copy video: \(error)")
                }
            }
        }
    }
}

// MARK: - Memorable Moments Section Component

struct MemorableMomentsSection: View {
    @Binding var text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("💭 ช่วงเวลาพิเศษ")
                    .font(.headline)
                Text("(optional)")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            Text("อะไรทำให้ช่วงเวลานี้พิเศษ?")
                .font(.caption)
                .foregroundColor(.gray)

            ZStack(alignment: .topLeading) {
                TextEditor(text: $text)
                    .frame(height: 80)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                    )

                if text.isEmpty {
                    Text("เช่น: ที่รักพาน้องไปร้านใหม่ที่น้องไม่เคยไป 💜")
                        .foregroundColor(.gray.opacity(0.5))
                        .font(.subheadline)
                        .padding(.horizontal, 8)
                        .padding(.top, 8)
                        .allowsHitTesting(false)
                }
            }
        }
    }
}

// MARK: - Image Captions Section Component

struct ImageCaptionsSection: View {
    let capturedImages: [UIImage]
    @Binding var imageCaptions: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("🖼️ คำบรรยายรูป")
                    .font(.headline)
                Text("(optional)")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            Text("เพิ่มคำบรรยายแต่ละรูป")
                .font(.caption)
                .foregroundColor(.gray)

            ForEach(capturedImages.indices, id: \.self) { index in
                ImageCaptionRow(
                    image: capturedImages[index],
                    index: index,
                    caption: captionBinding(for: index)
                )
            }
        }
    }

    private func captionBinding(for index: Int) -> Binding<String> {
        Binding(
            get: {
                index < imageCaptions.count ? imageCaptions[index] : ""
            },
            set: { newValue in
                while imageCaptions.count <= index {
                    imageCaptions.append("")
                }
                imageCaptions[index] = newValue
            }
        )
    }
}

struct ImageCaptionRow: View {
    let image: UIImage
    let index: Int
    @Binding var caption: String

    var body: some View {
        HStack(spacing: 12) {
            // Thumbnail
            Image(uiImage: image)
                .resizable()
                .scaledToFill()
                .frame(width: 60, height: 60)
                .clipped()
                .cornerRadius(8)

            // Caption input
            VStack(alignment: .leading, spacing: 4) {
                Text("รูปที่ \(index + 1)")
                    .font(.caption)
                    .foregroundColor(.gray)

                TextField("คำบรรยาย...", text: $caption)
                    .textFieldStyle(.roundedBorder)
                    .font(.subheadline)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    @Previewable @State var selectedTab = 0
    QuickCaptureView(selectedTab: $selectedTab)
        .environmentObject(DatabaseService.shared)
}
