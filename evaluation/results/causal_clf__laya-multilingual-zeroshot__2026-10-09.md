# causal_clf — laya-multilingual-zeroshot

Test set: `training/data/mit_eval.jsonl` (160 risks). Checkpoint `convaiinnovations/laya-multilingual` @ 1720e3e335. Run 2026-10-09 on cpu · 1.70 s per risk (3 questions) · commit `902e6bf`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 31.2 [24.4–38.8] | 27.7 [21.1–34.2] | 35.0 | 0.905 | 38.8 / 18.6 (`ai`) |
| intent | 45.6 [38.8–53.8] | 41.7 [33.4–49.4] | 20.5 | 0.708 | 40.6 / 19.3 (`unintentional`) |
| timing | 26.2 [19.4–32.5] | 19.5 [14.7–24.3] | 25.7 | 0.771 | 65.0 / 26.3 (`post-deployment`) |

All three axes correct: 3.8%.

Per-class F1 % (gold support):

- **entity**: ai 10.5 (n=62), human 42.7 (n=66), other 29.8 (n=32)
- **intent**: intentional 53.5 (n=57), unintentional 43.4 (n=65), other 28.1 (n=38)
- **timing**: pre-deployment 0.0 (n=18), post-deployment 24.5 (n=104), other 34.0 (n=38)
