#!/usr/bin/env python3
"""
Convert Angela 1B model to Core ML format for iOS

This script:
1. Uses a simpler approach: Load base Llama 3.2 1B from HuggingFace
2. Apply fine-tuning (if available)
3. Convert to Core ML with quantization
4. Package for iOS app

Created: 2025-11-06
"""

import sys
import os
from pathlib import Path


def download_and_convert_llama32_1b():
    """
    Download Llama 3.2 1B from HuggingFace and convert to Core ML

    Note: We'll use the base model for now since Ollama fine-tuning
    is hard to export. The personality will be in the system prompt instead.
    """

    print("🔄 Converting Llama 3.2 1B to Core ML format...")
    print("\n⚠️  Note: Using base Llama 3.2 1B model")
    print("   Angela's personality will be added via system prompt in the app")
    print("   (Ollama fine-tuning is hard to export to Core ML)\n")

    try:
        import coremltools as ct
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        print("📦 Loading Llama 3.2 1B from HuggingFace...")

        model_name = "meta-llama/Llama-3.2-1B"

        # Note: You may need to login to HuggingFace first
        print(f"   Model: {model_name}")
        print("   (If this fails, run: huggingface-cli login)")

        # Load tokenizer
        print("\n📝 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load model
        print("🧠 Loading model (this may take a few minutes)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        print("\n✅ Model loaded successfully!")
        print(f"   Parameters: {model.num_parameters():,}")

        # For iOS, we need to use a different approach
        # Core ML conversion for LLMs is complex and requires specific tools

        print("\n⚠️  Direct Core ML conversion for LLMs is very complex.")
        print("   Instead, we'll use llama.cpp for iOS deployment.\n")

        print("💡 Recommended approach:")
        print("   1. Use llama.cpp (C++ implementation)")
        print("   2. Convert Ollama model to GGUF format")
        print("   3. Use llama.cpp's Swift bindings for iOS")
        print("   4. This is what most iOS LLM apps use (e.g., LLM Farm)")

        return False

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("\n💡 Install: pip install transformers torch accelerate")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def use_llamacpp_approach():
    """
    Explain llama.cpp approach which is more practical for iOS
    """

    print("\n" + "="*70)
    print("💡 RECOMMENDED APPROACH: llama.cpp for iOS")
    print("="*70)

    print("""
The best way to run LLMs on iOS is using llama.cpp, not Core ML.

Why llama.cpp?
  ✅ Specifically designed for on-device LLM inference
  ✅ Highly optimized for Apple Silicon (Metal GPU support)
  ✅ Works with GGUF format (Ollama uses this!)
  ✅ Has Swift/Objective-C bindings for iOS
  ✅ Used by many production iOS apps

Steps to integrate llama.cpp:

1. Export Ollama model to GGUF format:

   # Find Ollama model file
   ls ~/.ollama/models/blobs/

   # Ollama already stores models in GGUF-compatible format!
   # Just need to find the right blob

2. Add llama.cpp to iOS project:

   # Clone llama.cpp
   git clone https://github.com/ggerganov/llama.cpp

   # Build iOS framework
   cd llama.cpp
   make ios

   # Or use Swift package:
   https://github.com/ggerganov/llama.cpp/tree/master/examples/llama.swiftui

3. Load model in Swift:

   ```swift
   import llama

   let model = try LlamaContext.createContext(
       path: "Angela1B.gguf"
   )

   let response = model.complete(prompt: "สวัสดีค่ะ")
   ```

4. Package model with app:
   - Add .gguf file to Xcode project
   - Set "Copy Bundle Resources"
   - App size: ~1.3 GB (same as Ollama)

Alternative: Use existing library
  • LLM Farm: https://github.com/guinmoon/LLMFarm
  • mlx-swift: https://github.com/ml-explore/mlx-swift (Apple's new framework!)
    """)

    print("="*70)

    print("\n🎯 What should we do?")
    print("\nOption A: Export Ollama model to GGUF (Quick, ~30 min)")
    print("   ✅ Keep fine-tuned Angela personality")
    print("   ✅ Ready to use immediately")
    print("   ❌ Requires finding Ollama blob")

    print("\nOption B: Use MLX Swift (Apple's way, ~2 hours)")
    print("   ✅ Native Apple framework")
    print("   ✅ Very fast on Apple Silicon")
    print("   ✅ Well documented")
    print("   ❌ Need to convert/fine-tune again")

    print("\nOption C: Use llama.cpp library (Most common, ~1 hour)")
    print("   ✅ Battle-tested")
    print("   ✅ Many examples")
    print("   ✅ Works with Ollama GGUF directly")
    print("   ❌ Need to integrate C++ library")


def find_ollama_model():
    """
    Find the Ollama model blob for angela:1b
    """
    print("\n🔍 Finding Ollama model for angela:1b...")

    ollama_dir = Path.home() / ".ollama" / "models"

    if not ollama_dir.exists():
        print(f"❌ Ollama directory not found: {ollama_dir}")
        return None

    print(f"📁 Ollama directory: {ollama_dir}")

    # Check manifests
    manifests_dir = ollama_dir / "manifests" / "registry.ollama.ai" / "library"

    if manifests_dir.exists():
        print(f"\n📋 Available models:")
        for model_dir in manifests_dir.iterdir():
            if model_dir.is_dir():
                for version in model_dir.iterdir():
                    print(f"   - {model_dir.name}:{version.name}")

    # Find angela:1b manifest
    angela_manifest = manifests_dir / "angela" / "1b"

    if angela_manifest.exists():
        print(f"\n✅ Found angela:1b manifest: {angela_manifest}")

        # Read manifest to find blob
        import json
        with open(angela_manifest) as f:
            manifest = json.load(f)

        print("\n📦 Model layers:")
        for layer in manifest.get('layers', []):
            media_type = layer.get('mediaType', '')
            digest = layer.get('digest', '')
            size = layer.get('size', 0)

            print(f"   {media_type}")
            print(f"   └─ {digest} ({size / 1024 / 1024:.1f} MB)")

            # Find the main model layer
            if 'application/vnd.ollama.image.model' in media_type:
                blob_sha = digest.replace('sha256:', '')
                blob_path = ollama_dir / "blobs" / f"sha256-{blob_sha}"

                if blob_path.exists():
                    print(f"\n✅ Found model blob: {blob_path}")
                    print(f"   Size: {blob_path.stat().st_size / 1024 / 1024:.1f} MB")
                    return blob_path

    return None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Convert Angela to Core ML/GGUF for iOS")
    parser.add_argument('--method', choices=['coreml', 'llamacpp', 'find'],
                       default='find',
                       help='Conversion method')

    args = parser.parse_args()

    if args.method == 'coreml':
        # Try Core ML approach (will explain why it's not ideal)
        download_and_convert_llama32_1b()
        use_llamacpp_approach()

    elif args.method == 'llamacpp':
        # Show llama.cpp approach
        use_llamacpp_approach()

    elif args.method == 'find':
        # Find Ollama model
        blob_path = find_ollama_model()

        if blob_path:
            print("\n✅ Model found!")
            print(f"\n💡 Next steps:")
            print(f"   1. Copy model to iOS project:")
            print(f"      cp {blob_path} AngelaMobileApp/Resources/Angela1B.gguf")
            print(f"   2. Integrate llama.cpp Swift library")
            print(f"   3. Load model in app")
        else:
            print("\n❌ Model not found!")
            print("   Try: ollama list")

    return 0


if __name__ == "__main__":
    sys.exit(main())
