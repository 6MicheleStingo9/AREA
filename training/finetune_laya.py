"""
Fine-tune Laya-multilingual on the MIT causal labels (training/data/causal_train.jsonl).

Wraps laya.train.finetune: RLCD objective (proper-scoring-rule reward plus soft cross-entropy),
a calibration slice held out from the training rows, temperatures fitted on it. Options are
shuffled each epoch so the model cannot learn a position prior. The checkpoint goes to
training/checkpoints/<name>/ (not versioned), with training_run.json recording the base
revision, the data checksum, the settings and the time taken; evaluate it with
training.evaluate_laya.

On CPU a full run takes about 15 hours (3.8 s per item measured on an i7-1255U, 12.5 GB of
RAM): train on a GPU, e.g. with training/kaggle_finetune.ipynb.

Usage (from the project root, training environment):
    python -m training.finetune_laya [--name laya-causal] [--epochs 4] [--device auto] [--limit N]
"""

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import snapshot_download
from laya.train import TrainConfig, finetune

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "training" / "data" / "causal_train.jsonl"
CHECKPOINTS = ROOT / "training" / "checkpoints"
BASE = "convaiinnovations/laya-multilingual"
BASE_REVISION = "1720e3e3357cfe1e281542e223f8273b0890ca34"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Laya-multilingual on the causal taxonomy")
    parser.add_argument("--name", default="laya-causal")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--micro-batch", type=int, default=8)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="auto", help="auto, cpu or cuda")
    parser.add_argument("--limit", type=int, default=None, help="Only the first N training rows (timing runs)")
    args = parser.parse_args()

    data = DATA
    if args.limit:
        data = DATA.with_name(f"causal_train.limit{args.limit}.jsonl")
        data.write_text("".join(DATA.read_text(encoding="utf-8").splitlines(keepends=True)[: args.limit]), encoding="utf-8")
    out = CHECKPOINTS / args.name
    config = TrainConfig(
        epochs=args.epochs,
        micro_batch=args.micro_batch,
        grad_accum=args.grad_accum,
        shuffle_options=("choice",),
        seed=args.seed,
    )
    base_dir = snapshot_download(BASE, revision=BASE_REVISION)
    t0 = time.time()
    summary = finetune(str(data), base_dir, str(out), config, device=args.device)
    run = {
        "base": BASE,
        "base_revision": BASE_REVISION,
        "data": str(data.relative_to(ROOT)),
        "data_sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
        "config": asdict(config),
        "device": args.device,
        "seconds": round(time.time() - t0, 1),
        "summary": summary,
    }
    (out / "training_run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"checkpoint: {out} ({run['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
