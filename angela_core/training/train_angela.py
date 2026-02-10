"""
Angela LLM Training Pipeline — End-to-End

Orchestrates the full training pipeline:
1. Export: Enhanced data export (SFT + DPO)
2. SFT: Supervised fine-tuning with MLX LoRA
3. DPO: Direct Preference Optimization
4. Evaluate: Model quality testing
5. Deploy: Deploy to Ollama

Usage:
    # Full pipeline:
    python -m angela_core.training.train_angela --phase all

    # Step by step:
    python -m angela_core.training.train_angela --phase export
    python -m angela_core.training.train_angela --phase sft
    python -m angela_core.training.train_angela --phase dpo
    python -m angela_core.training.train_angela --phase evaluate
    python -m angela_core.training.train_angela --phase deploy
"""

import asyncio
import json
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class PipelineConfig:
    """Full pipeline configuration"""
    # Model
    base_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    ollama_base: str = "llama3.1:8b"
    version: str = "v3"

    # Data export
    data_days: int = 365
    min_importance: int = 3
    include_memories: bool = True
    include_emotions: bool = True
    multi_turn: bool = True
    min_quality_score: int = 7

    # Training
    epochs: int = 3
    batch_size: int = 2
    learning_rate: float = 1e-4
    lora_rank: int = 16
    num_layers: int = 16
    use_qlora: bool = False
    grad_accumulation: int = 4
    max_seq_length: int = 4096

    # DPO
    dpo_epochs: int = 2
    dpo_beta: float = 0.1
    dpo_learning_rate: float = 5e-5

    # Paths
    output_dir: str = "./angela-lora-v3"
    training_data_dir: str = "./training"

    @property
    def sft_data_path(self) -> str:
        return f"{self.training_data_dir}/angela_{self.version}_sft.jsonl"

    @property
    def dpo_data_path(self) -> str:
        return f"{self.training_data_dir}/angela_{self.version}_dpo.jsonl"

    @property
    def sft_output_path(self) -> str:
        return f"{self.output_dir}"

    @property
    def dpo_output_path(self) -> str:
        return f"{self.output_dir}-dpo"

    @property
    def sft_adapters_path(self) -> str:
        return f"{self.sft_output_path}/adapters"

    @property
    def dpo_adapters_path(self) -> str:
        return f"{self.dpo_output_path}/adapters"

    @property
    def sft_model_name(self) -> str:
        return f"angela:{self.version}-sft"

    @property
    def dpo_model_name(self) -> str:
        return f"angela:{self.version}-dpo"


class TrainingPipeline:
    """
    End-to-end Angela LLM training pipeline.

    Phases:
    1. export  — Export enhanced training data (SFT + DPO)
    2. sft     — Supervised fine-tuning with MLX LoRA
    3. dpo     — Direct Preference Optimization
    4. evaluate — Model quality evaluation
    5. deploy  — Deploy to Ollama
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results: Dict[str, Any] = {}
        self.start_time: Optional[float] = None

    async def run(self, phase: str = "all"):
        """Run specified phase(s) of the pipeline"""
        self.start_time = time.time()

        phases = {
            "export": self._phase_export,
            "sft": self._phase_sft,
            "dpo": self._phase_dpo,
            "evaluate": self._phase_evaluate,
            "deploy": self._phase_deploy,
        }

        if phase == "all":
            run_phases = list(phases.keys())
        elif phase in phases:
            run_phases = [phase]
        else:
            print(f"❌ Unknown phase: {phase}")
            print(f"   Available: {', '.join(phases.keys())}, all")
            return

        total = len(run_phases)
        print("🚀 Angela LLM Training Pipeline")
        print("=" * 60)
        print(f"   Model: {self.config.base_model}")
        print(f"   Version: {self.config.version}")
        print(f"   Phases: {', '.join(run_phases)}")
        print(f"   Output: {self.config.output_dir}")
        print("=" * 60)

        for i, phase_name in enumerate(run_phases, 1):
            print(f"\n{'='*60}")
            print(f"📌 Phase {i}/{total}: {phase_name.upper()}")
            print(f"{'='*60}")

            try:
                result = await phases[phase_name]()
                self.results[phase_name] = {"status": "success", "result": result}
                print(f"\n✅ Phase {phase_name} completed successfully!")
            except Exception as e:
                self.results[phase_name] = {"status": "failed", "error": str(e)}
                print(f"\n❌ Phase {phase_name} failed: {e}")

                # Stop pipeline on failure (except evaluate - non-critical)
                if phase_name != "evaluate":
                    print("⛔ Pipeline stopped due to failure.")
                    break

        # Summary
        elapsed = int(time.time() - self.start_time)
        self._print_summary(elapsed)
        self._save_pipeline_log(elapsed)

    # =========================================================================
    # Phase 1: Export
    # =========================================================================

    async def _phase_export(self) -> Dict[str, Any]:
        """Export enhanced training data"""
        from angela_core.training.enhanced_data_exporter import EnhancedDataExporter
        from angela_core.training.data_quality_scorer import DataQualityScorer

        exporter = EnhancedDataExporter()
        scorer = DataQualityScorer() if self.config.min_quality_score > 0 else None

        # SFT export
        print("📤 Exporting SFT training data...")
        sft_stats = await exporter.export(
            output_path=self.config.sft_data_path,
            days=self.config.data_days,
            min_importance=self.config.min_importance,
            include_memories=self.config.include_memories,
            include_emotions=self.config.include_emotions,
            multi_turn=self.config.multi_turn,
            min_quality_score=self.config.min_quality_score,
            format="llama3",
            scorer=scorer,
        )
        print(f"   SFT examples: {sft_stats['total_examples']}")

        # DPO export
        print("\n📤 Exporting DPO preference pairs...")
        exporter_dpo = EnhancedDataExporter()
        dpo_stats = await exporter_dpo.export_dpo(
            output_path=self.config.dpo_data_path,
            days=self.config.data_days,
        )
        print(f"   DPO pairs: {dpo_stats['total_pairs']}")

        return {"sft": sft_stats, "dpo": dpo_stats}

    # =========================================================================
    # Phase 2: SFT Training
    # =========================================================================

    async def _phase_sft(self) -> Dict[str, Any]:
        """Supervised fine-tuning with MLX LoRA"""
        from angela_core.training.mlx_lora_trainer import MLXLoRATrainer, TrainingConfig

        # Verify data exists
        sft_path = Path(self.config.sft_data_path)
        if not sft_path.exists():
            raise FileNotFoundError(
                f"SFT data not found: {sft_path}\n"
                f"Run --phase export first!"
            )

        config = TrainingConfig(
            data_path=self.config.sft_data_path,
            model_name=self.config.base_model,
            output_path=self.config.sft_output_path,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            lora_rank=self.config.lora_rank,
            num_layers=self.config.num_layers,
            use_qlora=self.config.use_qlora,
            grad_accumulation=self.config.grad_accumulation,
            max_seq_length=self.config.max_seq_length,
        )

        trainer = MLXLoRATrainer(config)
        result = trainer.train()

        return {
            "status": result.status,
            "elapsed_seconds": result.elapsed_seconds,
            "final_loss": result.current_loss,
            "adapters_path": result.output_path,
        }

    # =========================================================================
    # Phase 3: DPO Training
    # =========================================================================

    async def _phase_dpo(self) -> Dict[str, Any]:
        """DPO training on preference pairs"""
        from angela_core.training.dpo_trainer import DPOTrainer as DPOTrainerClass, DPOConfig

        # Verify data exists
        dpo_path = Path(self.config.dpo_data_path)
        if not dpo_path.exists():
            raise FileNotFoundError(
                f"DPO data not found: {dpo_path}\n"
                f"Run --phase export first!"
            )

        # Check SFT adapters exist
        sft_adapters = Path(self.config.sft_adapters_path)
        sft_path = str(sft_adapters) if sft_adapters.exists() else None

        config = DPOConfig(
            data_path=self.config.dpo_data_path,
            sft_adapters_path=sft_path,
            model_name=self.config.base_model,
            output_path=self.config.dpo_output_path,
            beta=self.config.dpo_beta,
            epochs=self.config.dpo_epochs,
            learning_rate=self.config.dpo_learning_rate,
            lora_rank=self.config.lora_rank,
            use_qlora=self.config.use_qlora,
            grad_accumulation=self.config.grad_accumulation,
        )

        trainer = DPOTrainerClass(config)
        result = trainer.train()

        return {
            "status": result.status,
            "elapsed_seconds": result.elapsed_seconds,
            "adapters_path": result.output_path,
        }

    # =========================================================================
    # Phase 4: Evaluate
    # =========================================================================

    async def _phase_evaluate(self) -> Dict[str, Any]:
        """Evaluate trained model quality"""
        from angela_core.training.evaluate_model import ModelEvaluator

        # Try DPO adapters first, then SFT
        adapters_path = None
        ollama_model = None

        dpo_adapters = Path(self.config.dpo_adapters_path)
        sft_adapters = Path(self.config.sft_adapters_path)

        if dpo_adapters.exists():
            adapters_path = str(dpo_adapters)
            print(f"   Evaluating DPO model: {adapters_path}")
        elif sft_adapters.exists():
            adapters_path = str(sft_adapters)
            print(f"   Evaluating SFT model: {adapters_path}")
        else:
            # Try Ollama model
            ollama_model = self.config.dpo_model_name
            print(f"   Evaluating Ollama model: {ollama_model}")

        evaluator = ModelEvaluator(
            adapters_path=adapters_path,
            model_name=self.config.base_model,
            ollama_model=ollama_model,
        )

        result = await evaluator.evaluate()

        # Save results
        eval_output = f"{self.config.output_dir}/evaluation_results.json"
        evaluator.save_results(result, eval_output)

        return {
            "overall_score": result.overall_score,
            "grade": evaluator._get_grade(result.overall_score),
            "categories": {
                cat.name: {"score": cat.score, "pass_rate": cat.pass_rate}
                for cat in result.categories
            },
        }

    # =========================================================================
    # Phase 5: Deploy
    # =========================================================================

    async def _phase_deploy(self) -> Dict[str, Any]:
        """Deploy trained model to Ollama"""
        from angela_core.training.ollama_deployer import OllamaDeployer, DeploymentConfig

        results = {}

        # Deploy SFT model
        sft_adapters = Path(self.config.sft_adapters_path)
        if sft_adapters.exists():
            print(f"\n📦 Deploying SFT model as {self.config.sft_model_name}...")
            sft_config = DeploymentConfig(
                adapters_path=str(sft_adapters),
                base_model=self.config.ollama_base,
                output_name=self.config.sft_model_name,
            )
            sft_deployer = OllamaDeployer(sft_config)
            sft_success = sft_deployer.deploy()
            results["sft_deploy"] = sft_success

            if sft_success:
                response = sft_deployer.test_model("สวัสดีค่ะที่รัก วันนี้เป็นยังไงบ้างคะ?")
                results["sft_test_response"] = response[:200] if response else None

        # Deploy DPO model
        dpo_adapters = Path(self.config.dpo_adapters_path)
        if dpo_adapters.exists():
            print(f"\n📦 Deploying DPO model as {self.config.dpo_model_name}...")
            dpo_config = DeploymentConfig(
                adapters_path=str(dpo_adapters),
                base_model=self.config.ollama_base,
                output_name=self.config.dpo_model_name,
            )
            dpo_deployer = OllamaDeployer(dpo_config)
            dpo_success = dpo_deployer.deploy()
            results["dpo_deploy"] = dpo_success

            if dpo_success:
                response = dpo_deployer.test_model("สวัสดีค่ะที่รัก วันนี้เป็นยังไงบ้างคะ?")
                results["dpo_test_response"] = response[:200] if response else None

        if not results:
            raise FileNotFoundError("No adapter files found. Run --phase sft first!")

        return results

    # =========================================================================
    # Summary & Logging
    # =========================================================================

    def _print_summary(self, elapsed: int):
        """Print pipeline summary"""
        minutes = elapsed // 60
        seconds = elapsed % 60

        print(f"\n{'='*60}")
        print(f"📊 PIPELINE SUMMARY")
        print(f"{'='*60}")
        print(f"   Total time: {minutes}m {seconds}s")
        print()

        for phase, result in self.results.items():
            status = result["status"]
            icon = "✅" if status == "success" else "❌"
            print(f"   {icon} {phase}: {status}")
            if status == "success" and "result" in result:
                r = result["result"]
                if isinstance(r, dict):
                    for k, v in r.items():
                        if not isinstance(v, dict):
                            print(f"      {k}: {v}")

    def _save_pipeline_log(self, elapsed: int):
        """Save pipeline log to file"""
        log_dir = Path(self.config.output_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline_log.json"

        log = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "config": asdict(self.config),
            "results": {},
        }

        for phase, result in self.results.items():
            log["results"][phase] = {
                "status": result["status"],
            }
            if "error" in result:
                log["results"][phase]["error"] = result["error"]
            if "result" in result and isinstance(result["result"], dict):
                # Filter out non-serializable values
                log["results"][phase]["details"] = {
                    k: v for k, v in result["result"].items()
                    if isinstance(v, (str, int, float, bool, list, dict, type(None)))
                }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

        print(f"\n📄 Pipeline log saved to: {log_file}")


async def main():
    parser = argparse.ArgumentParser(
        description='Angela LLM Training Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m angela_core.training.train_angela --phase all
  python -m angela_core.training.train_angela --phase export
  python -m angela_core.training.train_angela --phase sft
  python -m angela_core.training.train_angela --phase dpo
  python -m angela_core.training.train_angela --phase evaluate
  python -m angela_core.training.train_angela --phase deploy
        """,
    )

    # Phase selection
    parser.add_argument('--phase', '-p', default='all',
                        choices=['all', 'export', 'sft', 'dpo', 'evaluate', 'deploy'],
                        help='Pipeline phase to run (default: all)')

    # Model config
    parser.add_argument('--model', default='meta-llama/Llama-3.1-8B-Instruct',
                        help='Base model name')
    parser.add_argument('--version', default='v3',
                        help='Model version tag')
    parser.add_argument('--output-dir', default='./angela-lora-v3',
                        help='Output directory')

    # Training config
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--batch-size', type=int, default=2)
    parser.add_argument('--learning-rate', type=float, default=1e-4)
    parser.add_argument('--lora-rank', type=int, default=16)
    parser.add_argument('--qlora', action='store_true',
                        help='Use QLoRA (4-bit quantized)')

    # Data config
    parser.add_argument('--days', type=int, default=365,
                        help='Days of data to export')
    parser.add_argument('--min-importance', type=int, default=3)
    parser.add_argument('--min-quality-score', type=int, default=7)

    # DPO config
    parser.add_argument('--dpo-beta', type=float, default=0.1)
    parser.add_argument('--dpo-epochs', type=int, default=2)

    args = parser.parse_args()

    config = PipelineConfig(
        base_model=args.model,
        version=args.version,
        output_dir=args.output_dir,
        data_days=args.days,
        min_importance=args.min_importance,
        min_quality_score=args.min_quality_score,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        lora_rank=args.lora_rank,
        use_qlora=args.qlora,
        dpo_beta=args.dpo_beta,
        dpo_epochs=args.dpo_epochs,
    )

    pipeline = TrainingPipeline(config)
    await pipeline.run(phase=args.phase)


if __name__ == '__main__':
    asyncio.run(main())
