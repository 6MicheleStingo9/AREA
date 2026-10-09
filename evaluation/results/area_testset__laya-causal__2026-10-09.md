# area_testset — laya-causal

Test set: `training/data/area_test.jsonl` (145 risks). Checkpoint `training/checkpoints/laya-causal`. Run 2026-10-09 on cuda · 0.03 s per risk (3 questions) · commit `de5c5de`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 68.3 [60.7–75.2] | 58.4 [49.4–66.9] | 6.8 | 0.428 | 54.5 / 23.5 (`ai`) |
| intent | 67.6 [60.0–75.2] | 60.8 [53.4–67.8] | 7.0 | 0.429 | 57.9 / 24.5 (`unintentional`) |
| timing | 77.2 [70.3–83.4] | 48.2 [34.9–62.5] | 17.3 | 0.355 | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 42.8%.

Per-class F1 % (gold support):

- **entity**: ai 75.3 (n=79), human 69.5 (n=51), other 30.3 (n=15)
- **intent**: intentional 85.3 (n=33), unintentional 74.1 (n=84), other 23.1 (n=28)
- **timing**: pre-deployment 25.0 (n=2), post-deployment 87.0 (n=132), other 32.6 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 72.9 / 63.9 | 68.2 / 59.0 | 76.5 / 37.2 |
| language=it | 60 | 61.7 / 49.9 | 66.7 / 62.3 | 78.3 / 56.5 |
| source=example | 34 | 79.4 / 71.6 | 67.6 / 58.7 | 73.5 / 39.0 |
| source=generated | 111 | 64.9 / 53.8 | 67.6 / 61.4 | 78.4 / 49.6 |
