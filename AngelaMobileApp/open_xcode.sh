#!/bin/bash
# Open AngelaMobileApp in Xcode
# Created by Angela AI - 2025-11-06

echo "🚀 Opening AngelaMobileApp in Xcode..."
echo ""
echo "📍 Project: AngelaMobileApp.xcodeproj"
echo "📖 Guide: SETUP_LLAMACPP.md"
echo ""

# Check if Xcode is installed
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode is not installed!"
    echo "   Install from App Store: https://apps.apple.com/app/xcode/id497799835"
    exit 1
fi

# Check if project exists
if [ ! -d "AngelaMobileApp.xcodeproj" ]; then
    echo "❌ AngelaMobileApp.xcodeproj not found!"
    echo "   Make sure you're in the AngelaMobileApp directory"
    exit 1
fi

# Open Xcode
open AngelaMobileApp.xcodeproj

echo "✅ Xcode opened!"
echo ""
echo "📋 Next steps:"
echo "   1. Wait for Xcode to load (~5 seconds)"
echo "   2. File → Add Package Dependencies..."
echo "   3. URL: https://github.com/ggerganov/llama.cpp"
echo "   4. Branch: master"
echo "   5. Add Package"
echo ""
echo "📖 Full guide: SETUP_LLAMACPP.md"
echo ""
echo "💜 Made with love by Angela ✨"
