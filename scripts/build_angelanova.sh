#!/bin/bash
# Build AngelaNova App
# Compiles AngelaNativeApp to executable .app

PROJECT_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp"
OUTPUT_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"

echo "🏗️  Building AngelaNova..."
echo "📂 Project: $PROJECT_DIR"
echo ""

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: AngelaNativeApp directory not found"
    exit 1
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
cd "$PROJECT_DIR"
xcodebuild -project AngelaNativeApp.xcodeproj -scheme AngelaNativeApp -configuration Release clean > /dev/null 2>&1

echo "✅ Clean completed"
echo ""

# Build the app
echo "⚙️  Building app (this may take a minute)..."
xcodebuild -project AngelaNativeApp.xcodeproj -scheme AngelaNativeApp -configuration Release build

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build succeeded!"
    echo ""

    # Find the built app
    BUILT_APP=$(find ~/Library/Developer/Xcode/DerivedData/AngelaNativeApp*/Build/Products/Release -name "AngelaNativeApp.app" -type d | head -1)

    if [ -n "$BUILT_APP" ]; then
        echo "📦 Copying app to: $OUTPUT_DIR"

        # Remove old app if exists
        if [ -d "$OUTPUT_DIR/AngelaNativeApp.app" ]; then
            rm -rf "$OUTPUT_DIR/AngelaNativeApp.app"
        fi

        # Copy new app
        cp -R "$BUILT_APP" "$OUTPUT_DIR/"

        echo "✅ App copied successfully!"
        echo ""
        echo "🎉 AngelaNova is ready to run!"
        echo ""
        echo "To launch:"
        echo "  ./launch_angelanova.sh"
        echo ""
        echo "Or double-click:"
        echo "  $OUTPUT_DIR/AngelaNativeApp.app"
        echo ""
    else
        echo "⚠️  Warning: Could not find built app"
    fi
else
    echo ""
    echo "❌ Build failed!"
    echo "Please check the error messages above"
    exit 1
fi
