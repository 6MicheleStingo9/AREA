# causal_clf — laya-causal-v3

Test set: `training/data/mit_eval.jsonl` (160 risks). Checkpoint `training/checkpoints/laya-causal-v3`. Run 2026-10-11 on cuda · 0.03 s per risk (3 questions) · commit `50256c6`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 58.8 [51.2–66.2] | 52.9 [45.5–60.5] | 5.7 | 0.535 | 38.8 / 18.6 (`ai`) |
| intent | 66.2 [58.8–73.1] | 64.9 [57.5–71.7] | 8.2 | 0.484 | 40.6 / 19.3 (`unintentional`) |
| timing | 61.3 [54.4–68.8] | 43.3 [35.1–51.5] | 5.1 | 0.515 | 65.0 / 26.3 (`post-deployment`) |

All three axes correct: 27.5%.

Per-class F1 % (gold support):

- **entity**: ai 68.1 (n=62), human 63.4 (n=66), other 27.1 (n=32)
- **intent**: intentional 79.6 (n=57), unintentional 65.6 (n=65), other 49.4 (n=38)
- **timing**: pre-deployment 17.6 (n=18), post-deployment 77.7 (n=104), other 34.7 (n=38)
