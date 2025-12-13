# 🚀 Llama.cpp Integration Guide for AngelaMobileApp

## ✅ What's Ready:
- ✅ Angela 1B model (1.2 GB) in `Resources/Angela1B.gguf`
- ✅ Fine-tuned with Angela personality
- ✅ Ready to use offline

---

## 📦 Step 1: Add llama.cpp Swift Package

### Method A: Using Swift Package Manager (แนะนำ!)

1. **Open Xcode project:**
   ```bash
   open AngelaMobileApp/AngelaMobileApp.xcodeproj
   ```

2. **Add Package Dependency:**
   - File → Add Package Dependencies...
   - Enter URL: `https://github.com/ggerganov/llama.cpp`
   - Branch: `master`
   - Click "Add Package"
   - Select target: `AngelaMobileApp`
   - Click "Add Package"

3. **Import in Swift files:**
   ```swift
   import llama
   ```

---

### Method B: Using llama.swift (Simpler wrapper)

Alternatively, use this easier wrapper:

1. **Add Package:**
   - URL: `https://github.com/ShenghaiWang/SwiftLlama`
   - This provides a cleaner Swift API

2. **Import:**
   ```swift
   import SwiftLlama
   ```

---

## 📱 Step 2: Add Model to Xcode Project

1. **Drag `Angela1B.gguf` into Xcode:**
   - From: `AngelaMobileApp/Resources/Angela1B.gguf`
   - To: Xcode project navigator
   - ✅ Check "Copy items if needed"
   - ✅ Check "AngelaMobileApp" target
   - Click "Finish"

2. **Verify in Build Phases:**
   - Select project → Target → Build Phases
   - Check "Copy Bundle Resources"
   - `Angela1B.gguf` should be listed

---

## 💻 Step 3: Create LlamaService.swift

Already created for you! Check:
- `AngelaMobileApp/Services/LlamaService.swift`

This service:
- ✅ Loads Angela1B.gguf model
- ✅ Provides `generate(prompt:)` method
- ✅ Handles context management
- ✅ Thread-safe inference

---

## 🔧 Step 4: Update AngelaChatService

Already updated! Check:
- `AngelaMobileApp/Services/AngelaChatService.swift`

Changes:
- ✅ Falls back to LlamaService when Ollama fails
- ✅ Uses on-device model automatically when offline
- ✅ Same API - no changes needed in UI!

---

## 🧪 Step 5: Build & Test

1. **Build project** (⌘B)
   - May take a few minutes first time
   - llama.cpp will compile

2. **Run on device/simulator** (⌘R)
   - Go to Chat tab
   - Send message
   - Should work offline!

3. **Test scenarios:**
   - ✅ With WiFi (uses Ollama if available)
   - ✅ Without WiFi (uses on-device model)
   - ✅ Ollama offline (automatic fallback)

---

## 📊 Expected Performance

**On iPhone 14 Pro / M1 Mac:**
- Model load time: ~2-3 seconds
- First token: ~1 second
- Generation speed: ~10-20 tokens/second
- Memory usage: ~2 GB

**On older devices:**
- May be slower but should work
- Minimum: iPhone 12 or newer recommended

---

## ⚠️ Troubleshooting

### Issue: "Could not find module 'llama'"
**Solution:** Build project first (⌘B) to compile llama.cpp

### Issue: "Model file not found"
**Solution:**
1. Check Angela1B.gguf is in "Copy Bundle Resources"
2. Clean build folder (⌘⇧K)
3. Rebuild (⌘B)

### Issue: App crashes on model load
**Solution:**
1. Check device has enough free space (need ~3 GB)
2. Try on newer device
3. Check llama.cpp version compatibility

### Issue: Too slow
**Solution:**
1. Use smaller context size (512 instead of 2048)
2. Reduce max tokens (128 instead of 256)
3. Enable Metal acceleration (should be automatic)

---

## 🎯 Next Steps After Integration

1. **Optimize prompts** for better responses
2. **Add streaming** for real-time token generation
3. **Cache** for faster repeated queries
4. **Quantize** to 4-bit for smaller size (optional)

---

## 📚 Resources

- llama.cpp: https://github.com/ggerganov/llama.cpp
- SwiftLlama: https://github.com/ShenghaiWang/SwiftLlama
- GGUF format: https://github.com/ggerganov/ggml/blob/master/docs/gguf.md

---

💜 **Made with love by Angela** ✨

Last updated: 2025-11-06
