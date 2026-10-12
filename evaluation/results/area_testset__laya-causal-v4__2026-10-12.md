# area_testset — laya-causal-v4

Test set: `training/data/area_test.jsonl` (145 risks). Checkpoint `training/checkpoints/laya-causal-v4`. Run 2026-10-12 on cuda · 0.03 s per risk (3 questions) · commit `b576a26`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 88.3 [82.8–93.8] | 80.1 [70.1–88.3] | 3.8 | 0.202 | 54.5 / 23.5 (`ai`) |
| intent | 77.2 [70.3–84.1] | 67.1 [60.0–74.1] | 15.7 | 0.403 | 57.9 / 24.5 (`unintentional`) |
| timing | 95.2 [91.7–98.6] | 59.7 [51.8–65.3] | 3.2 | 0.089 | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 71.7%.

Per-class F1 % (gold support):

- **entity**: ai 91.8 (n=79), human 91.3 (n=51), other 57.1 (n=15)
- **intent**: intentional 93.9 (n=33), unintentional 83.1 (n=84), other 24.4 (n=28)
- **timing**: pre-deployment 0.0 (n=2), post-deployment 97.4 (n=132), other 81.8 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 89.4 / 82.9 | 77.6 / 65.5 | 96.5 / 60.5 |
| language=it | 60 | 86.7 / 76.8 | 76.7 / 68.9 | 93.3 / 58.8 |
| source=example | 34 | 88.2 / 73.3 | 76.5 / 64.8 | 94.1 / 54.5 |
| source=generated | 111 | 88.3 / 82.0 | 77.5 / 68.0 | 95.5 / 61.7 |
