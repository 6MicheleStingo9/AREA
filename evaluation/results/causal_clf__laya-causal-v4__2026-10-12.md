# causal_clf — laya-causal-v4

Test set: `training/data/mit_eval.jsonl` (160 risks). Checkpoint `training/checkpoints/laya-causal-v4`. Run 2026-10-12 on cuda · 0.04 s per risk (3 questions) · commit `b576a26`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 61.3 [53.1–68.8] | 52.6 [45.0–59.5] | 26.9 | 0.634 | 38.8 / 18.6 (`ai`) |
| intent | 61.9 [53.8–69.4] | 58.7 [50.8–65.8] | 29.6 | 0.656 | 40.6 / 19.3 (`unintentional`) |
| timing | 65.6 [58.8–73.1] | 48.4 [39.1–57.6] | 24.2 | 0.592 | 65.0 / 26.3 (`post-deployment`) |

All three axes correct: 30.0%.

Per-class F1 % (gold support):

- **entity**: ai 69.4 (n=62), human 68.3 (n=66), other 20.0 (n=32)
- **intent**: intentional 74.3 (n=57), unintentional 67.1 (n=65), other 34.7 (n=38)
- **timing**: pre-deployment 32.4 (n=18), post-deployment 80.5 (n=104), other 32.3 (n=38)
