# causal_clf — laya-causal

Test set: `training/data/mit_eval.jsonl` (160 risks). Checkpoint `training/checkpoints/laya-causal`. Run 2026-10-09 on cuda · 0.04 s per risk (3 questions) · commit `de5c5de`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 52.5 [44.4–60.0] | 47.2 [39.1–54.8] | 13.7 | 0.612 | 38.8 / 18.6 (`ai`) |
| intent | 65.0 [57.5–72.5] | 63.9 [56.4–71.3] | 6.5 | 0.452 | 40.6 / 19.3 (`unintentional`) |
| timing | 64.4 [57.5–71.9] | 43.9 [35.2–52.9] | 6.6 | 0.468 | 65.0 / 26.3 (`post-deployment`) |

All three axes correct: 26.2%.

Per-class F1 % (gold support):

- **entity**: ai 58.3 (n=62), human 57.4 (n=66), other 25.9 (n=32)
- **intent**: intentional 77.1 (n=57), unintentional 64.6 (n=65), other 50.0 (n=38)
- **timing**: pre-deployment 17.4 (n=18), post-deployment 78.2 (n=104), other 36.1 (n=38)
