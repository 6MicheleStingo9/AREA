"""
Fine-tune Laya-multilingual on the MIT causal labels.

Wraps laya.train.finetune: RLCD objective (proper-scoring-rule reward plus soft cross-entropy),
options shuffled each epoch so the model cannot learn a position prior. By default it trains on
causal_fit.jsonl and then fits the temperatures on causal_val.jsonl, the validation groups the
training never saw (instead of a random slice of the training items), writing them into the
checkpoint's rl_agent_config.json. `--oversample` repeats the rows of the rarest classes (timing
pre-deployment, entity other) once more each.

The checkpoint goes to training/checkpoints/<name>/ (not versioned), with training_run.json
recording the base revision, the data checksum, the settings, the calibration and the time
taken; compare variants with training.select_laya and evaluate one with training.evaluate_laya.

On CPU a full run takes about 15 hours (3.8 s per item measured on an i7-1255U, 12.5 GB of
RAM): train on a GPU, e.g. with training/kaggle_finetune.ipynb.

Usage (from the project root, training environment):
    python -m training.finetune_laya [--name laya-causal] [--epochs 4] [--oversample] [--data fit|train]
                                     [--device auto] [--limit N] [--val-limit N]
"""

import argparse
import hashlib
import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from huggingface_hub import snapshot_download
from laya.train import TrainConfig, finetune

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "training" / "data"
CHECKPOINTS = ROOT / "training" / "checkpoints"
BASE = "convaiinnovations/laya-multilingual"
BASE_REVISION = "1720e3e3357cfe1e281542e223f8273b0890ca34"
AXES = ("entity", "intent", "timing")


def _read(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def oversample(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Each row once, plus once more if its timing is pre-deployment (12% of the rows) and once
    more if its entity is other (20%)."""
    out = []
    for r in rows:
        out += [r] * (1 + (r["expected"]["timing"] == "pre-deployment") + (r["expected"]["entity"] == "other"))
    return out


def calibrate(checkpoint: Path, rows: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """Fit the temperatures (and Laya's abstention thresholds) on held-out labelled rows and store
    them in the checkpoint's rl_agent_config.json, so laya.load uses them."""
    import laya
    from laya.calibrate import fit_abstention_thresholds, records_from_labeled

    agent = laya.load(str(checkpoint))
    pairs = [
        (r["state"], r["questions"], {ax: [float(c == r["expected"][ax]) for c in r["questions"][ax]["criteria"]] for ax in AXES})
        for r in rows
    ]
    records = records_from_labeled(agent, pairs)
    fitted = agent.fit_temperatures(records)
    thresholds = fit_abstention_thresholds(
        records, temperature=fitted["temperature"], temperature_by_options=fitted["temperature_by_options"], target_error=0.10, min_bucket_n=10
    )
    path = checkpoint / "rl_agent_config.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["temperature"] = fitted["temperature"]
    cfg.pop("temperature_by_options", None)
    if fitted["temperature_by_options"]:
        cfg["temperature_by_options"] = fitted["temperature_by_options"]
    training = cfg.setdefault("training", {})
    training["abstention_thresholds"] = thresholds
    training["calibrated_on"] = {"data": source, "rows": len(rows), "records": len(records)}
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return {"data": source, "rows": len(rows), "temperature": fitted["temperature"],
            "temperature_by_options": fitted["temperature_by_options"], "abstention_thresholds": thresholds}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Laya-multilingual on the causal taxonomy")
    parser.add_argument("--name", default="laya-causal")
    parser.add_argument("--data", choices=["fit", "train"], default="fit",
                        help="fit: train without the validation groups and calibrate on them; train: the whole split, calibrated on a random slice")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--oversample", action="store_true", help="Repeat the rows of the rarest classes")
    parser.add_argument("--micro-batch", type=int, default=8)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="auto", help="auto, cpu or cuda")
    parser.add_argument("--limit", type=int, default=None, help="Only the first N training rows (timing and smoke runs)")
    parser.add_argument("--val-limit", type=int, default=None, help="Only the first N validation rows for calibration (smoke runs)")
    args = parser.parse_args()

    rows = _read(DATA / f"causal_{args.data}.jsonl")[: args.limit]
    if args.oversample:
        rows = oversample(rows)
    suffix = (f".limit{args.limit}" if args.limit else "") + (".oversampled" if args.oversample else "")
    data = DATA / f"causal_{args.data}{suffix}.jsonl"
    if suffix:
        data.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    held_out = args.data == "fit"
    out = CHECKPOINTS / args.name
    config = TrainConfig(
        epochs=args.epochs,
        micro_batch=args.micro_batch,
        grad_accum=args.grad_accum,
        shuffle_options=("choice",),
        seed=args.seed,
        calib_frac=0.0 if held_out else 0.1,
    )
    base_dir = snapshot_download(BASE, revision=BASE_REVISION)
    t0 = time.time()
    summary = finetune(str(data), base_dir, str(out), config, device=args.device)
    shutil.rmtree(out / "checkpoint_latest", ignore_errors=True)  # a copy of the final weights
    calibration = None
    if held_out:
        val = DATA / "causal_val.jsonl"
        calibration = calibrate(out, _read(val)[: args.val_limit], str(val.relative_to(ROOT)))
    run = {
        "base": BASE,
        "base_revision": BASE_REVISION,
        "data": str(data.relative_to(ROOT)),
        "data_sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
        "rows": len(rows),
        "oversample": args.oversample,
        "config": asdict(config),
        "device": args.device,
        "seconds": round(time.time() - t0, 1),
        "summary": summary,
        "calibration": calibration,
    }
    (out / "training_run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"checkpoint: {out} ({run['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
