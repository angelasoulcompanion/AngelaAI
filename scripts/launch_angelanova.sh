#!/bin/bash
# Launch AngelaNova App
# This script opens the compiled AngelaNativeApp

APP_PATH="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp.app"

echo "🚀 Launching AngelaNova..."
echo "📍 App location: $APP_PATH"
echo ""

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: AngelaNativeApp.app not found at $APP_PATH"
    echo ""
    echo "Please compile the app first:"
    echo "  cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaNativeApp"
    echo "  xcodebuild -project AngelaNativeApp.xcodeproj -scheme AngelaNativeApp -configuration Release build"
    exit 1
fi

# Open the app
echo "✅ Opening AngelaNova..."
open "$APP_PATH"

echo "💜 AngelaNova is starting!"
echo ""
echo "Note: Make sure the backend is running:"
echo "  python3 -m angela_backend.main"
echo ""
