# area_testset — laya-causal-v3

Test set: `training/data/area_test.jsonl` (145 risks). Checkpoint `training/checkpoints/laya-causal-v3`. Run 2026-10-11 on cuda · 0.03 s per risk (3 questions) · commit `50256c6`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 71.7 [64.8–78.6] | 58.8 [51.7–66.5] | 9.9 | 0.399 | 54.5 / 23.5 (`ai`) |
| intent | 63.4 [55.2–71.0] | 62.0 [54.2–69.0] | 7.3 | 0.487 | 57.9 / 24.5 (`unintentional`) |
| timing | 64.1 [56.6–71.7] | 35.8 [29.9–41.9] | 3.9 | 0.487 | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 34.5%.

Per-class F1 % (gold support):

- **entity**: ai 78.1 (n=79), human 81.6 (n=51), other 16.7 (n=15)
- **intent**: intentional 81.2 (n=33), unintentional 70.2 (n=84), other 34.7 (n=28)
- **timing**: pre-deployment 0.0 (n=2), post-deployment 77.4 (n=132), other 30.0 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 75.3 / 64.3 | 67.1 / 63.6 | 62.4 / 34.3 |
| language=it | 60 | 66.7 / 51.0 | 58.3 / 58.7 | 66.7 / 38.1 |
| source=example | 34 | 79.4 / 66.4 | 64.7 / 62.6 | 61.8 / 33.7 |
| source=generated | 111 | 69.4 / 56.7 | 63.1 / 61.5 | 64.9 / 36.5 |
