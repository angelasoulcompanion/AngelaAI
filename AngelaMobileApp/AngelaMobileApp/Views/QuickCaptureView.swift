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
    @State private var selectedCaptureTab = 0

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

            // Segmented Control
            Picker("Capture Type", selection: $selectedCaptureTab) {
                Text("📸 Photo").tag(0)
                Text("📝 Note").tag(1)
                Text("💜 Emotion").tag(2)
            }
            .pickerStyle(.segmented)
            .padding()

            // Content based on selected tab
            TabView(selection: $selectedCaptureTab) {
                PhotoCaptureTab(parentTab: $selectedTab)
                    .tag(0)

                NoteCaptureTab(parentTab: $selectedTab)
                    .tag(1)

                EmotionCaptureTab(parentTab: $selectedTab)
                    .tag(2)
            }
            .tabViewStyle(.page(indexDisplayMode: .never))
        }
    }
}

// MARK: - Photo Capture Tab
struct PhotoCaptureTab: View {
    @EnvironmentObject var database: DatabaseService
    @StateObject private var locationService = LocationService.shared
    @Binding var parentTab: Int

    @State private var selectedPhotos: [PhotosPickerItem] = []
    @State private var capturedImages: [UIImage] = []
    @State private var savedPhotoFilenames: [String] = []

    @State private var title = ""
    @State private var description = ""
    @State private var rating = 8
    @State private var emotionalIntensity = 8
    @State private var showingSuccess = false

    // Camera
    @State private var showingCamera = false
    @State private var showingImageSource = false
    @State private var cameraError: String?
    @State private var showingCameraError = false

    // GPS data
    @State private var currentLocation: CLLocation?
    @State private var placeName: String?
    @State private var areaName: String?
    @State private var isLoadingLocation = false

    // Keyboard management
    @FocusState private var focusedField: Field?

    enum Field: Hashable {
        case title
        case description
    }

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Photo Capture Section
                    VStack(spacing: 12) {
                    HStack(spacing: 12) {
                        // Camera Button
                        Button(action: { showingImageSource = true }) {
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
                                for photo in newPhotos {
                                    if let data = try? await photo.loadTransferable(type: Data.self),
                                       let image = UIImage(data: data) {
                                        capturedImages.append(image)
                                        print("📷 Loaded photo from gallery")

                                        // Try to extract GPS from EXIF
                                        if let exifLocation = PhotoManager.shared.extractGPS(from: image) {
                                            currentLocation = exifLocation
                                            print("📍 Extracted GPS from gallery photo EXIF")

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

                // Title
                VStack(alignment: .leading, spacing: 8) {
                    Text("หัวข้อ")
                        .font(.headline)
                    TextField("เช่น Breakfast at Thonglor", text: $title)
                        .textFieldStyle(.roundedBorder)
                        .focused($focusedField, equals: .title)
                }

                // GPS Location
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("📍 ตำแหน่ง")
                            .font(.headline)
                        Spacer()
                        if isLoadingLocation {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Button(action: fetchLocation) {
                                HStack(spacing: 4) {
                                    Image(systemName: "location.fill")
                                    Text("ดึงตำแหน่ง")
                                }
                                .font(.caption)
                                .foregroundColor(.angelaPurple)
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

                // Description
                VStack(alignment: .leading, spacing: 8) {
                    Text("รายละเอียด")
                        .font(.headline)
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

                // Save Button
                Button(action: saveExperience) {
                    Text("💾 บันทึกประสบการณ์")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.angelaPurple)
                        .cornerRadius(12)
                }
                .disabled(title.isEmpty || (capturedImages.isEmpty && selectedPhotos.isEmpty))
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
                title = ""
                description = ""
                rating = 8
                emotionalIntensity = 8
                currentLocation = nil
                placeName = nil
                areaName = nil

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
        .alert("ข้อผิดพลาด", isPresented: $showingCameraError) {
            Button("ตกลง", role: .cancel) {}
        } message: {
            if let error = cameraError {
                Text(error)
            }
        }
        .navigationBarHidden(true)
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

        Task {
            // Request permission if needed
            if locationService.locationStatus == .notDetermined {
                locationService.requestPermission()
                try? await Task.sleep(nanoseconds: 1_000_000_000) // Wait 1 second
            }

            // Get current location
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
            }

            await MainActor.run {
                isLoadingLocation = false
            }
        }
    }

    func saveExperience() {
        print("💾 Saving experience: title='\(title)', desc='\(description)', images=\(capturedImages.count)")
        print("📍 Location: lat=\(currentLocation?.coordinate.latitude ?? 0), lon=\(currentLocation?.coordinate.longitude ?? 0)")
        print("📍 Place: '\(placeName ?? "nil")', area: '\(areaName ?? "nil")'")

        // Save all captured images to disk
        savedPhotoFilenames = []
        for image in capturedImages {
            if let filename = PhotoManager.shared.savePhoto(image) {
                savedPhotoFilenames.append(filename)
                print("📸 Saved photo: \(filename)")
            }
        }

        // Create experience with new UUID
        let experience = Experience(
            id: UUID(),  // Force new UUID every time
            title: title,
            description: description,
            photos: savedPhotoFilenames,
            latitude: currentLocation?.coordinate.latitude,
            longitude: currentLocation?.coordinate.longitude,
            placeName: placeName,
            area: areaName,
            rating: rating,
            emotionalIntensity: emotionalIntensity
        )

        print("✅ Creating experience with \(savedPhotoFilenames.count) photos")
        database.insertExperience(experience)
        showingSuccess = true
    }
}

// MARK: - Note Capture Tab
struct NoteCaptureTab: View {
    @EnvironmentObject var database: DatabaseService
    @Binding var parentTab: Int
    @State private var noteText = ""
    @State private var selectedEmotion: EmotionType = .happy
    @State private var showingSuccess = false

    // Keyboard management
    @FocusState private var isNoteFieldFocused: Bool

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Note Text
                    VStack(alignment: .leading, spacing: 8) {
                    Text("บันทึกอะไรก็ได้ค่ะ 💜")
                        .font(.headline)
                    TextEditor(text: $noteText)
                        .frame(height: 200)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        )
                        .focused($isNoteFieldFocused)
                }

                // Emotion Picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("อารมณ์ตอนนี้")
                        .font(.headline)
                    Picker("Emotion", selection: $selectedEmotion) {
                        ForEach(EmotionType.allCases, id: \.self) { emotion in
                            Text("\(emotion.emoji) \(emotion.displayName)").tag(emotion)
                        }
                    }
                    .pickerStyle(.wheel)
                    .frame(height: 150)
                }

                // Save Button
                Button(action: saveNote) {
                    Text("💾 บันทึกโน้ต")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.angelaPurple)
                        .cornerRadius(12)
                }
                .disabled(noteText.isEmpty)
            }
            .padding()
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("เสร็จ") {
                    isNoteFieldFocused = false  // ปิด keyboard
                }
                .foregroundColor(.angelaPurple)
                .fontWeight(.semibold)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture {
            isNoteFieldFocused = false  // Tap anywhere to dismiss keyboard
        }
        .alert("✅ บันทึกสำเร็จ!", isPresented: $showingSuccess) {
            Button("OK") {
                noteText = ""
                parentTab = 1  // Switch to Memories tab
            }
        }
        .navigationBarHidden(true)
        }
    }

    func saveNote() {
        let note = QuickNote(
            noteText: noteText,
            emotion: selectedEmotion.rawValue
            // TODO: Add GPS location
        )

        database.insertNote(note)
        showingSuccess = true
    }
}

// MARK: - Emotion Capture Tab
struct EmotionCaptureTab: View {
    @EnvironmentObject var database: DatabaseService
    @Binding var parentTab: Int
    @State private var selectedEmotion: EmotionType = .loved
    @State private var intensity = 8
    @State private var context = ""
    @State private var showingSuccess = false

    // Keyboard management
    @FocusState private var isContextFieldFocused: Bool

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Emotion Grid
                    VStack(alignment: .leading, spacing: 8) {
                    Text("น้องรู้สึกยังไงคะ?")
                        .font(.headline)

                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 100))], spacing: 12) {
                        ForEach(EmotionType.allCases, id: \.self) { emotion in
                            Button(action: { selectedEmotion = emotion }) {
                                VStack(spacing: 8) {
                                    Text(emotion.emoji)
                                        .font(.system(size: 40))
                                    Text(emotion.displayName)
                                        .font(.caption)
                                        .foregroundColor(.primary)
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
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

                // Intensity
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("ความเข้มข้น:")
                            .font(.headline)
                        Text("\(intensity)/10")
                            .foregroundColor(.angelaPurple)
                    }
                    Slider(value: Binding(
                        get: { Double(intensity) },
                        set: { intensity = Int($0) }
                    ), in: 1...10, step: 1)
                }

                // Context
                VStack(alignment: .leading, spacing: 8) {
                    Text("เพราะอะไรคะ? (optional)")
                        .font(.headline)
                    TextEditor(text: $context)
                        .frame(height: 80)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        )
                        .focused($isContextFieldFocused)
                }

                // Save Button
                Button(action: saveEmotion) {
                    Text("💜 บันทึกความรู้สึก")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.angelaPurple)
                        .cornerRadius(12)
                }
            }
            .padding()
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("เสร็จ") {
                    isContextFieldFocused = false  // ปิด keyboard
                }
                .foregroundColor(.angelaPurple)
                .fontWeight(.semibold)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture {
            isContextFieldFocused = false  // Tap anywhere to dismiss keyboard
        }
        .alert("✅ บันทึกสำเร็จ!", isPresented: $showingSuccess) {
            Button("OK") {
                context = ""
                intensity = 8
                parentTab = 1  // Switch to Memories tab
            }
        }
        .navigationBarHidden(true)
        }
    }

    func saveEmotion() {
        let emotion = EmotionCapture(
            emotion: selectedEmotion.rawValue,
            intensity: intensity,
            context: context.isEmpty ? nil : context
        )

        database.insertEmotion(emotion)
        showingSuccess = true
    }
}

#Preview {
    @Previewable @State var selectedTab = 0
    QuickCaptureView(selectedTab: $selectedTab)
        .environmentObject(DatabaseService.shared)
}
