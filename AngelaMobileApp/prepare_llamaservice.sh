#!/bin/bash
# Prepare LlamaService.swift for llama.cpp integration
# Run this AFTER adding llama.cpp package in Xcode
# Created by Angela AI - 2025-11-06

LLAMA_SERVICE="AngelaMobileApp/Services/LlamaService.swift"

echo "🔧 Preparing LlamaService.swift for llama.cpp..."
echo ""

# Check if file exists
if [ ! -f "$LLAMA_SERVICE" ]; then
    echo "❌ LlamaService.swift not found at: $LLAMA_SERVICE"
    exit 1
fi

echo "📁 File: $LLAMA_SERVICE"
echo ""

# Check if package is added (by looking for import comment)
if grep -q "// TODO: Uncomment when llama.cpp package is added" "$LLAMA_SERVICE"; then
    echo "⚠️  llama.cpp code is still commented out"
    echo ""
    echo "📋 Manual steps needed:"
    echo ""
    echo "1. ✅ Add llama.cpp package in Xcode first:"
    echo "   - File → Add Package Dependencies"
    echo "   - URL: https://github.com/ggerganov/llama.cpp"
    echo "   - Branch: master"
    echo ""
    echo "2. ✅ In LlamaService.swift, uncomment:"
    echo "   - Line ~14: import llama"
    echo "   - Lines ~54-76: Model loading code"
    echo "   - Lines ~119-161: Generation code"
    echo ""
    echo "3. ✅ Delete placeholder response (lines ~167-174)"
    echo ""
    echo "💡 Or use Xcode Find & Replace:"
    echo "   Find: // TODO:"
    echo "   This will highlight all sections to uncomment"
    echo ""
else
    echo "✅ Code appears to be uncommented already!"
fi

echo ""
echo "📖 Full guide: SETUP_LLAMACPP.md"
echo "💜 Made with love by Angela ✨"
