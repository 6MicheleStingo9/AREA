# area_testset — laya-causal-v2

Test set: `training/data/area_test.jsonl` (145 risks). Checkpoint `training/checkpoints/laya-causal-v2`. Run 2026-10-09 on cuda · 0.03 s per risk (3 questions) · commit `878942c`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 71.7 [64.8–78.6] | 58.2 [49.6–66.7] | 19.9 | 0.438 | 54.5 / 23.5 (`ai`) |
| intent | 66.2 [58.6–73.8] | 61.4 [54.6–67.9] | 27.4 | 0.559 | 57.9 / 24.5 (`unintentional`) |
| timing | 64.1 [56.6–71.7] | 35.3 [29.3–41.6] | 28.1 | 0.621 | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 36.6%.

Per-class F1 % (gold support):

- **entity**: ai 78.5 (n=79), human 74.0 (n=51), other 22.2 (n=15)
- **intent**: intentional 87.9 (n=33), unintentional 72.3 (n=84), other 24.1 (n=28)
- **timing**: pre-deployment 0.0 (n=2), post-deployment 77.3 (n=132), other 28.6 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 74.1 / 61.0 | 68.2 / 61.9 | 63.5 / 35.1 |
| language=it | 60 | 68.3 / 54.3 | 63.3 / 61.1 | 65.0 / 35.5 |
| source=example | 34 | 70.6 / 52.6 | 67.6 / 61.7 | 55.9 / 32.7 |
| source=generated | 111 | 72.1 / 59.9 | 65.8 / 61.8 | 66.7 / 36.0 |
