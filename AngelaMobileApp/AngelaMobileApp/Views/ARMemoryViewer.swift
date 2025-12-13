//
//  ARMemoryViewer.swift
//  Angela Mobile App
//
//  AR viewer for memories using RealityKit
//  Feature 29: AR Memory Viewer
//

import SwiftUI
import RealityKit
import ARKit

struct ARMemoryViewer: View {
    @EnvironmentObject var database: DatabaseService
    @State private var selectedExperience: Experience?
    @State private var showingPicker = false

    var body: some View {
        ZStack {
            // AR View
            ARViewContainer(experience: selectedExperience)
                .ignoresSafeArea()

            // UI Overlay
            VStack {
                // Header
                HStack {
                    Button(action: { showingPicker = true }) {
                        HStack(spacing: 8) {
                            Image(systemName: "photo.stack")
                            Text(selectedExperience?.title ?? "เลือกความทรงจำ")
                                .lineLimit(1)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(Color.white.opacity(0.9))
                        .cornerRadius(25)
                        .shadow(radius: 4)
                    }
                    .foregroundColor(.angelaPurple)

                    Spacer()
                }
                .padding()

                Spacer()

                // Instructions
                if selectedExperience != nil {
                    VStack(spacing: 8) {
                        Text("👆 แตะบนพื้นเพื่อวางรูป")
                            .font(.caption)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.black.opacity(0.7))
                            .foregroundColor(.white)
                            .cornerRadius(20)

                        Text("🤏 หยิกเพื่อซูม • หมุนได้")
                            .font(.caption2)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.black.opacity(0.7))
                            .foregroundColor(.white.opacity(0.8))
                            .cornerRadius(15)
                    }
                    .padding(.bottom, 32)
                }
            }
        }
        .sheet(isPresented: $showingPicker) {
            MemoryPickerView(selectedExperience: $selectedExperience)
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - AR View Container

struct ARViewContainer: UIViewRepresentable {
    let experience: Experience?

    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)

        // Configure AR session
        let config = ARWorldTrackingConfiguration()
        config.planeDetection = [.horizontal, .vertical]
        arView.session.run(config)

        // Add tap gesture
        let tapGesture = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.handleTap(_:)))
        arView.addGestureRecognizer(tapGesture)

        context.coordinator.arView = arView

        return arView
    }

    func updateUIView(_ uiView: ARView, context: Context) {
        context.coordinator.currentExperience = experience
    }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    // MARK: - Coordinator

    class Coordinator: NSObject {
        var arView: ARView?
        var currentExperience: Experience?
        var placedEntities: [AnchorEntity] = []

        @objc func handleTap(_ recognizer: UITapGestureRecognizer) {
            guard let arView = arView,
                  let experience = currentExperience,
                  !experience.photos.isEmpty,
                  let firstPhoto = experience.photos.first,
                  let image = PhotoManager.shared.loadPhoto(firstPhoto) else {
                return
            }

            let tapLocation = recognizer.location(in: arView)

            // Perform raycast to find surface
            let results = arView.raycast(from: tapLocation, allowing: .estimatedPlane, alignment: .any)

            guard let firstResult = results.first else { return }

            // Create anchor at tapped location
            let anchor = AnchorEntity(world: firstResult.worldTransform)

            // Create image plane
            let mesh = MeshResource.generatePlane(width: 0.3, depth: 0.4)

            // Convert UIImage to Material
            if let cgImage = image.cgImage {
                var material = SimpleMaterial()

                // Create texture from CGImage (iOS 18+ compatible)
                if #available(iOS 18.0, *) {
                    // New API for iOS 18+
                    if let textureResource = try? TextureResource(image: cgImage, options: .init(semantic: .color)) {
                        material.color = .init(tint: .white, texture: .init(textureResource))
                        material.metallic = .float(0.0)
                        material.roughness = .float(1.0)

                        let modelEntity = ModelEntity(mesh: mesh, materials: [material])

                        // Add slight tilt for better viewing
                        modelEntity.orientation = simd_quatf(angle: -.pi / 12, axis: [1, 0, 0])

                        // Add to anchor
                        anchor.addChild(modelEntity)

                        // Add anchor to scene
                        arView.scene.addAnchor(anchor)

                        placedEntities.append(anchor)

                        print("✅ AR Memory placed!")
                    }
                } else {
                    // Fallback for iOS 17 and earlier
                    if let textureResource = try? TextureResource.generate(from: cgImage, options: .init(semantic: .color)) {
                        material.color = .init(tint: .white, texture: .init(textureResource))
                        material.metallic = .float(0.0)
                        material.roughness = .float(1.0)

                        let modelEntity = ModelEntity(mesh: mesh, materials: [material])

                        // Add slight tilt for better viewing
                        modelEntity.orientation = simd_quatf(angle: -.pi / 12, axis: [1, 0, 0])

                        // Add to anchor
                        anchor.addChild(modelEntity)

                        // Add anchor to scene
                        arView.scene.addAnchor(anchor)

                        placedEntities.append(anchor)

                        print("✅ AR Memory placed!")
                    }
                }
            }
        }

        func clearAllEntities() {
            for entity in placedEntities {
                entity.removeFromParent()
            }
            placedEntities.removeAll()
        }
    }
}

// MARK: - Memory Picker View

struct MemoryPickerView: View {
    @EnvironmentObject var database: DatabaseService
    @Binding var selectedExperience: Experience?
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            List(database.experiences.filter { !$0.photos.isEmpty }) { experience in
                Button(action: {
                    selectedExperience = experience
                    dismiss()
                }) {
                    HStack(spacing: 12) {
                        // Thumbnail
                        if let firstPhoto = experience.photos.first,
                           let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                            Image(uiImage: image)
                                .resizable()
                                .scaledToFill()
                                .frame(width: 60, height: 60)
                                .clipped()
                                .cornerRadius(8)
                        }

                        // Info
                        VStack(alignment: .leading, spacing: 4) {
                            Text(experience.title)
                                .font(.headline)
                                .foregroundColor(.primary)

                            Text(experience.experiencedAt.formatted(date: .abbreviated, time: .omitted))
                                .font(.caption)
                                .foregroundColor(.gray)

                            if let place = experience.placeName {
                                Text(place)
                                    .font(.caption)
                                    .foregroundColor(.angelaPurple)
                            }
                        }

                        Spacer()

                        if selectedExperience?.id == experience.id {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.angelaPurple)
                        }
                    }
                }
            }
            .navigationTitle("เลือกความทรงจำ")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("เสร็จ") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    NavigationView {
        ARMemoryViewer()
            .environmentObject(DatabaseService.shared)
    }
}
