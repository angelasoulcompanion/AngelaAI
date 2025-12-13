//
//  ServicesTestView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-07.
//  Quick test view for all services
//

import SwiftUI

struct ServicesTestView: View {
    @State private var isRunning = false
    @State private var testLog = ""
    @State private var showLog = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                // Header
                VStack(spacing: 10) {
                    Image(systemName: "testtube.2")
                        .font(.system(size: 60))
                        .foregroundColor(.purple)

                    Text("Angela Services Test")
                        .font(.title)
                        .fontWeight(.bold)

                    Text("Test Calendar, Contacts, and Core ML")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding()

                Spacer()

                // Test Buttons
                VStack(spacing: 20) {
                    // Run All Tests Button
                    Button {
                        runAllTests()
                    } label: {
                        HStack {
                            if isRunning {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Image(systemName: "play.fill")
                            }

                            Text(isRunning ? "Running Tests..." : "Run All Tests")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(Color.purple)
                        .foregroundColor(.white)
                        .cornerRadius(16)
                    }
                    .disabled(isRunning)

                    // Individual Test Buttons
                    HStack(spacing: 15) {
                        TestButton(
                            icon: "calendar",
                            title: "Calendar",
                            color: .blue,
                            isRunning: isRunning
                        ) {
                            runCalendarTest()
                        }

                        TestButton(
                            icon: "person.crop.circle",
                            title: "Contacts",
                            color: .green,
                            isRunning: isRunning
                        ) {
                            runContactsTest()
                        }

                        TestButton(
                            icon: "brain",
                            title: "Core ML",
                            color: .orange,
                            isRunning: isRunning
                        ) {
                            runCoreMLTest()
                        }
                    }
                }
                .padding(.horizontal)

                Spacer()

                // View Log Button
                if !testLog.isEmpty {
                    Button {
                        showLog = true
                    } label: {
                        HStack {
                            Image(systemName: "doc.text")
                            Text("View Test Log")
                        }
                        .foregroundColor(.purple)
                    }
                }

                // Instructions
                VStack(alignment: .leading, spacing: 8) {
                    Text("Instructions:")
                        .font(.headline)

                    Text("• Grant permissions when prompted")
                    Text("• Check Xcode console for detailed output")
                    Text("• Test results appear in real-time")
                }
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
                .padding(.horizontal)

            }
            .navigationTitle("Service Tests")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showLog) {
                NavigationStack {
                    ScrollView {
                        Text(testLog)
                            .font(.system(.caption, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding()
                    }
                    .navigationTitle("Test Log")
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .navigationBarTrailing) {
                            Button("Done") {
                                showLog = false
                            }
                        }
                    }
                }
            }
        }
    }

    // MARK: - Test Functions

    private func runAllTests() {
        isRunning = true
        testLog = ""

        Task {
            await SimpleServicesTest.runAllTests()

            await MainActor.run {
                isRunning = false
                testLog = "All tests completed! Check Xcode console for details."
            }
        }
    }

    private func runCalendarTest() {
        isRunning = true
        testLog = ""

        Task {
            await SimpleServicesTest.testCalendarService()

            await MainActor.run {
                isRunning = false
                testLog = "Calendar test completed! Check Xcode console."
            }
        }
    }

    private func runContactsTest() {
        isRunning = true
        testLog = ""

        Task {
            await SimpleServicesTest.testContactsService()

            await MainActor.run {
                isRunning = false
                testLog = "Contacts test completed! Check Xcode console."
            }
        }
    }

    private func runCoreMLTest() {
        isRunning = true

        Task {
            await MainActor.run {
                SimpleServicesTest.testCoreMLService()
                isRunning = false
                testLog = "Core ML test completed! Check Xcode console."
            }
        }
    }
}

// MARK: - Test Button Component

struct TestButton: View {
    let icon: String
    let title: String
    let color: Color
    let isRunning: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)

                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 80)
            .background(color.opacity(0.1))
            .foregroundColor(color)
            .cornerRadius(12)
        }
        .disabled(isRunning)
    }
}

// MARK: - Preview

#Preview {
    ServicesTestView()
}
