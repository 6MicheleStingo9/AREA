# causal_clf — laya-causal-v2

Test set: `training/data/mit_eval.jsonl` (160 risks). Checkpoint `training/checkpoints/laya-causal-v2`. Run 2026-10-09 on cuda · 0.04 s per risk (3 questions) · commit `878942c`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 58.8 [50.6–66.2] | 50.6 [42.5–58.0] | 32.9 | 0.731 | 38.8 / 18.6 (`ai`) |
| intent | 65.0 [57.5–72.5] | 63.2 [55.5–70.7] | 26.7 | 0.590 | 40.6 / 19.3 (`unintentional`) |
| timing | 59.4 [51.9–66.9] | 46.3 [36.6–54.4] | 32.7 | 0.698 | 65.0 / 26.3 (`post-deployment`) |

All three axes correct: 27.5%.

Per-class F1 % (gold support):

- **entity**: ai 66.2 (n=62), human 66.2 (n=66), other 19.6 (n=32)
- **intent**: intentional 76.2 (n=57), unintentional 66.7 (n=65), other 46.8 (n=38)
- **timing**: pre-deployment 36.8 (n=18), post-deployment 75.0 (n=104), other 27.0 (n=38)
