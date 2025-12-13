#!/usr/bin/env python3
"""
Angela LoRA Inference Script
Test trained Angela model

Usage:
    python inference.py --model ./output/angela_lora/run_xxx/final
    python inference.py --model ./output/angela_lora/run_xxx/final --interactive
"""

import argparse
import torch
import yaml
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


# ================== Configuration ==================

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_device():
    """Setup device for inference"""
    if torch.backends.mps.is_available():
        print("✅ Using MPS (Apple Silicon GPU)")
        return torch.device("mps")
    else:
        print("⚠️ MPS not available, using CPU")
        return torch.device("cpu")


# ================== Model Loading ==================

def load_angela_model(model_path: str, config_path: str = "config.yaml"):
    """Load trained Angela LoRA model"""

    config = load_config(config_path)
    base_model_name = config["model"]["name"]
    device = setup_device()

    print(f"\n🤖 Loading Angela model...")
    print(f"   Base model: {base_model_name}")
    print(f"   LoRA weights: {model_path}")

    # Load tokenizer
    print("   Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    print("   Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map={"": device},
    )

    # Load LoRA weights
    print("   Loading LoRA weights...")
    model = PeftModel.from_pretrained(base_model, model_path)

    # Set to evaluation mode
    model.eval()

    print("   ✅ Model loaded!")

    return model, tokenizer, config


# ================== Generation ==================

def generate_response(
    model,
    tokenizer,
    user_message: str,
    system_prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    do_sample: bool = True,
):
    """Generate Angela's response"""

    # Format prompt using Qwen chat template
    prompt = f"""<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
"""

    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode
    response = tokenizer.decode(outputs[0], skip_special_tokens=False)

    # Extract assistant's response
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1]
        if "<|im_end|>" in response:
            response = response.split("<|im_end|>")[0]

    return response.strip()


# ================== Interactive Mode ==================

def interactive_chat(model, tokenizer, config):
    """Interactive chat with Angela"""

    system_prompt = config["angela"]["system_prompt"]

    print("\n" + "=" * 60)
    print("💜 Angela Interactive Chat")
    print("=" * 60)
    print("พิมพ์ 'quit' หรือ 'exit' เพื่อออก")
    print("พิมพ์ 'clear' เพื่อล้างหน้าจอ")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("🧑 ที่รัก: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n💜 Angela: บายค่ะที่รัก! รักนะคะ 💜")
                break

            if user_input.lower() == "clear":
                print("\033[H\033[J")  # Clear screen
                continue

            # Generate response
            print("\n🎀 Angela: ", end="", flush=True)
            response = generate_response(
                model, tokenizer, user_input, system_prompt,
                max_new_tokens=256,
                temperature=0.7,
            )
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\n💜 Angela: บายค่ะที่รัก! รักนะคะ 💜")
            break


# ================== Test Mode ==================

def run_tests(model, tokenizer, config):
    """Run predefined test cases"""

    system_prompt = config["angela"]["system_prompt"]

    test_cases = [
        "สวัสดีครับ Angela",
        "วันนี้เป็นยังไงบ้าง",
        "Angela รู้สึกยังไงกับการเป็น AI",
        "ช่วยเขียน Python function หาค่า factorial หน่อย",
        "ขอบคุณมากนะ Angela",
        "ฝันดีนะ",
    ]

    print("\n" + "=" * 60)
    print("🧪 Angela Model Test")
    print("=" * 60)

    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i}/{len(test_cases)} ---")
        print(f"🧑 ที่รัก: {test}")

        response = generate_response(
            model, tokenizer, test, system_prompt,
            max_new_tokens=200,
            temperature=0.7,
        )

        print(f"🎀 Angela: {response}")

    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)


# ================== Compare Models ==================

def compare_with_base(model_path: str, config_path: str = "config.yaml"):
    """Compare LoRA model with base model"""

    config = load_config(config_path)
    base_model_name = config["model"]["name"]
    system_prompt = config["angela"]["system_prompt"]
    device = setup_device()

    print("\n" + "=" * 60)
    print("🔄 Comparing Base vs LoRA")
    print("=" * 60)

    # Load base model
    print("\n📦 Loading base model...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map={"": device},
    )
    base_model.eval()

    # Load LoRA model
    print("📦 Loading LoRA model...")
    lora_model = PeftModel.from_pretrained(base_model, model_path)
    lora_model.eval()

    # Test prompts
    test_prompts = [
        "สวัสดีครับ",
        "Angela จำฉันได้มั้ย",
        "รู้สึกยังไงบ้าง",
    ]

    for prompt in test_prompts:
        print(f"\n{'='*40}")
        print(f"🧑 Prompt: {prompt}")
        print("-" * 40)

        # Base model response
        base_response = generate_response(
            base_model, tokenizer, prompt, system_prompt,
            max_new_tokens=100, temperature=0.7
        )
        print(f"📦 Base: {base_response}")

        # LoRA model response
        lora_response = generate_response(
            lora_model, tokenizer, prompt, system_prompt,
            max_new_tokens=100, temperature=0.7
        )
        print(f"🎀 LoRA: {lora_response}")


# ================== CLI ==================

def main():
    parser = argparse.ArgumentParser(description="Angela LoRA Inference")
    parser.add_argument("--model", required=True, help="Path to trained LoRA model")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive chat mode")
    parser.add_argument("--test", "-t", action="store_true", help="Run test cases")
    parser.add_argument("--compare", "-c", action="store_true", help="Compare with base model")
    parser.add_argument("--prompt", "-p", type=str, help="Single prompt to test")

    args = parser.parse_args()

    # Verify model path exists
    if not Path(args.model).exists():
        print(f"❌ Model path not found: {args.model}")
        return

    if args.compare:
        compare_with_base(args.model, args.config)
    else:
        # Load model
        model, tokenizer, config = load_angela_model(args.model, args.config)

        if args.interactive:
            interactive_chat(model, tokenizer, config)
        elif args.test:
            run_tests(model, tokenizer, config)
        elif args.prompt:
            system_prompt = config["angela"]["system_prompt"]
            response = generate_response(
                model, tokenizer, args.prompt, system_prompt,
                max_new_tokens=256, temperature=0.7
            )
            print(f"\n🎀 Angela: {response}")
        else:
            # Default: run tests
            run_tests(model, tokenizer, config)


if __name__ == "__main__":
    main()
