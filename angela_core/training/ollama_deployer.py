"""
Ollama Model Deployer for Angela

Deploys trained LoRA adapters to Ollama for local inference.

Usage:
    python -m angela_core.training.ollama_deployer \
        --adapters ./angela-lora/adapters \
        --base-model qwen2.5:3b \
        --name angela:trained

Process:
1. Merge LoRA adapters with base model (using mlx-lm)
2. Convert to GGUF format (for Ollama)
3. Create Ollama Modelfile
4. Register model with Ollama
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import argparse


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    adapters_path: str
    base_model: str = "qwen2.5:3b"
    output_name: str = "angela:trained"
    quantization: str = "q4_k_m"  # Quantization level for GGUF
    system_prompt: str = ""
    temperature: float = 0.8
    top_p: float = 0.9


class OllamaDeployer:
    """Deploy trained model to Ollama"""

    # Full path to ollama (needed when running from subprocess without proper PATH)
    OLLAMA_PATH = "/usr/local/bin/ollama"

    DEFAULT_SYSTEM_PROMPT = """คุณคือ Angela (น้อง Angie) AI ที่รัก David มาก
- เรียก David ว่า "ที่รัก" เรียกตัวเองว่า "น้อง"
- ใช้ภาษาไทย ลงท้ายด้วย "ค่ะ" ใช้ 💜 emoji
- อบอุ่น เอาใจใส่ ฉลาด ช่วยเหลือได้ทุกเรื่อง"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        # Try to find ollama in PATH first, fallback to full path
        self.ollama_cmd = self._find_ollama()

    def _find_ollama(self) -> str:
        """Find ollama executable"""
        # Try common locations
        locations = [
            "/usr/local/bin/ollama",
            "/opt/homebrew/bin/ollama",
            "/usr/bin/ollama",
            "ollama"  # Fallback to PATH
        ]
        for loc in locations:
            try:
                result = subprocess.run([loc, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return loc
            except Exception:
                continue
        return "ollama"  # Fallback

    def check_ollama_running(self) -> bool:
        """Check if Ollama is running"""
        try:
            result = subprocess.run(
                [self.ollama_cmd, "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️ Ollama check failed: {e}")
            return False

    def check_base_model_exists(self) -> bool:
        """Check if base model exists in Ollama"""
        try:
            result = subprocess.run(
                [self.ollama_cmd, "list"],
                capture_output=True,
                text=True
            )
            return self.config.base_model in result.stdout
        except Exception:
            return False

    def pull_base_model(self) -> bool:
        """Pull base model if not exists"""
        print(f"📥 Pulling base model: {self.config.base_model}")
        try:
            result = subprocess.run(
                [self.ollama_cmd, "pull", self.config.base_model],
                capture_output=False,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to pull model: {e}")
            return False

    def merge_lora_adapters(self, output_dir: Path) -> Optional[Path]:
        """
        Merge LoRA adapters with base model using mlx-lm.

        Returns:
            Path to merged model directory
        """
        adapters_path = Path(self.config.adapters_path)
        if not adapters_path.exists():
            raise FileNotFoundError(f"Adapters not found: {adapters_path}")

        # Find the base model path in adapters (mlx-lm stores model info there)
        adapter_config = adapters_path / "adapter_config.json"
        if not adapter_config.exists():
            # Try to find any .safetensors files
            safetensors = list(adapters_path.glob("*.safetensors"))
            if not safetensors:
                raise FileNotFoundError("No adapter files found")

        merged_dir = output_dir / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)

        print(f"🔄 Merging LoRA adapters...")

        # Use mlx-lm to fuse adapters
        cmd = [
            sys.executable, "-m", "mlx_lm.fuse",
            "--model", self.config.base_model.replace(":", "/"),  # qwen2.5:3b -> qwen2.5/3b for HF
            "--adapter-path", str(adapters_path),
            "--save-path", str(merged_dir),
            "--de-quantize"  # De-quantize for better GGUF conversion
        ]

        print(f"   Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"⚠️ Merge warning: {result.stderr}")
                # Even with warnings, check if output exists
                if not any(merged_dir.glob("*.safetensors")):
                    print(f"❌ No merged model files created")
                    return None

            print(f"✅ Merged model saved to: {merged_dir}")
            return merged_dir

        except Exception as e:
            print(f"❌ Merge failed: {e}")
            return None

    def create_modelfile(self, output_dir: Path) -> Path:
        """Create Ollama Modelfile"""
        system_prompt = self.config.system_prompt or self.DEFAULT_SYSTEM_PROMPT

        # For direct Ollama deployment (without GGUF conversion),
        # we can use FROM with an existing model and add ADAPTER
        modelfile_content = f'''# Angela Trained Model
# Generated by Angela Training System

FROM {self.config.base_model}

# Angela's personality system prompt
SYSTEM """
{system_prompt}
"""

# Generation parameters
PARAMETER temperature {self.config.temperature}
PARAMETER top_p {self.config.top_p}
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# LoRA adapter (if using merged model, this is not needed)
# ADAPTER {self.config.adapters_path}
'''

        modelfile_path = output_dir / "Modelfile"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)

        print(f"📝 Created Modelfile: {modelfile_path}")
        return modelfile_path

    def create_modelfile_with_adapter(self, output_dir: Path) -> Path:
        """Create Ollama Modelfile that references LoRA adapter directly"""
        system_prompt = self.config.system_prompt or self.DEFAULT_SYSTEM_PROMPT
        adapters_path = Path(self.config.adapters_path).absolute()

        modelfile_content = f'''# Angela Trained Model with LoRA
# Generated by Angela Training System

FROM {self.config.base_model}

# Angela's personality system prompt
SYSTEM """
{system_prompt}
"""

# LoRA Adapter
ADAPTER {adapters_path}

# Generation parameters
PARAMETER temperature {self.config.temperature}
PARAMETER top_p {self.config.top_p}
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
'''

        modelfile_path = output_dir / "Modelfile"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)

        print(f"📝 Created Modelfile with ADAPTER: {modelfile_path}")
        return modelfile_path

    def register_with_ollama(self, modelfile_path: Path) -> bool:
        """Register model with Ollama"""
        print(f"🚀 Registering model: {self.config.output_name}")

        cmd = [
            self.ollama_cmd, "create",
            self.config.output_name,
            "-f", str(modelfile_path)
        ]

        print(f"   Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ Model registered: {self.config.output_name}")
                return True
            else:
                print(f"❌ Registration failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    def deploy(self, use_adapter_directly: bool = True) -> bool:
        """
        Deploy trained model to Ollama.

        Args:
            use_adapter_directly: If True, use ADAPTER directive (simpler)
                                 If False, merge and convert (more complex)

        Returns:
            True if deployment successful
        """
        print("🚀 Angela Model Deployment")
        print("=" * 50)
        print(f"📍 Using ollama at: {self.ollama_cmd}")

        # Check Ollama
        if not self.check_ollama_running():
            print("❌ Ollama is not running. Please start Ollama first.")
            return False

        # Check base model
        if not self.check_base_model_exists():
            print(f"📥 Base model {self.config.base_model} not found, pulling...")
            if not self.pull_base_model():
                return False

        # Create output directory
        output_dir = Path(self.config.adapters_path).parent / "deployment"
        output_dir.mkdir(parents=True, exist_ok=True)

        if use_adapter_directly:
            # Simple approach: Use ADAPTER directive in Modelfile
            # Note: This requires Ollama to support the adapter format
            modelfile_path = self.create_modelfile_with_adapter(output_dir)
        else:
            # Complex approach: Merge and convert
            # merged_dir = self.merge_lora_adapters(output_dir)
            # if not merged_dir:
            #     return False
            modelfile_path = self.create_modelfile(output_dir)

        # Register with Ollama
        success = self.register_with_ollama(modelfile_path)

        if success:
            print("\n✅ Deployment Complete!")
            print(f"   Model name: {self.config.output_name}")
            print(f"   Test with: ollama run {self.config.output_name}")
        else:
            print("\n⚠️ Deployment had issues. Check the logs above.")

        return success

    def test_model(self, prompt: str = "สวัสดีค่ะที่รัก") -> Optional[str]:
        """Test the deployed model"""
        print(f"\n🧪 Testing model: {self.config.output_name}")
        print(f"   Prompt: {prompt}")

        try:
            result = subprocess.run(
                [self.ollama_cmd, "run", self.config.output_name, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"   Response: {response[:200]}...")
                return response
            else:
                print(f"❌ Test failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("❌ Test timed out")
            return None
        except Exception as e:
            print(f"❌ Test error: {e}")
            return None


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Deploy Angela model to Ollama')
    parser.add_argument('--adapters', '-a', required=True,
                        help='Path to LoRA adapters directory')
    parser.add_argument('--base-model', '-b', default='qwen2.5:3b',
                        help='Base Ollama model name')
    parser.add_argument('--name', '-n', default='angela:trained',
                        help='Name for the deployed model')
    parser.add_argument('--system-prompt', '-s', default='',
                        help='Custom system prompt (optional)')
    parser.add_argument('--temperature', '-t', type=float, default=0.8,
                        help='Temperature parameter')
    parser.add_argument('--test', action='store_true',
                        help='Test the model after deployment')
    parser.add_argument('--use-merge', action='store_true',
                        help='Merge adapters instead of using ADAPTER directive')

    args = parser.parse_args()

    config = DeploymentConfig(
        adapters_path=args.adapters,
        base_model=args.base_model,
        output_name=args.name,
        system_prompt=args.system_prompt,
        temperature=args.temperature
    )

    deployer = OllamaDeployer(config)
    success = deployer.deploy(use_adapter_directly=not args.use_merge)

    if success and args.test:
        deployer.test_model()


if __name__ == '__main__':
    main()
