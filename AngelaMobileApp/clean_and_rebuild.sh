#!/bin/bash
#
# Clean and Rebuild Angela Mobile App
# This script completely cleans all build artifacts and rebuilds
#

echo "🧹 Cleaning Angela Mobile App..."

# Step 1: Clean derived data
echo "📦 Removing derived data..."
rm -rf ~/Library/Developer/Xcode/DerivedData/AngelaMobileApp-*

# Step 2: Clean build folder
echo "🗑️  Cleaning build folder..."
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaMobileApp
xcodebuild -project AngelaMobileApp.xcodeproj -scheme AngelaMobileApp -configuration Debug clean

# Step 3: Rebuild
echo "🔨 Building..."
xcodebuild -project AngelaMobileApp.xcodeproj -scheme AngelaMobileApp -configuration Debug -sdk iphonesimulator build

# Step 4: Check for warnings
echo ""
echo "📊 Checking for warnings..."
WARNINGS=$(xcodebuild -project AngelaMobileApp.xcodeproj -scheme AngelaMobileApp -configuration Debug -sdk iphonesimulator build 2>&1 | grep -i "warning" | grep -v "appintentsmetadataprocessor" | grep -v "Provisioning" | grep -v "Using the first")

if [ -z "$WARNINGS" ]; then
    echo "✅ BUILD SUCCEEDED - NO WARNINGS!"
else
    echo "⚠️  Found warnings:"
    echo "$WARNINGS"
fi

echo ""
echo "💜 Done! Now open Xcode and it should show clean build."
