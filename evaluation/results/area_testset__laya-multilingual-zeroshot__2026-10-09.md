# area_testset — laya-multilingual-zeroshot

Test set: `training/data/area_test.jsonl` (145 risks). Checkpoint `convaiinnovations/laya-multilingual` @ 1720e3e335. Run 2026-10-09 on cpu · 1.68 s per risk (3 questions) · commit `902e6bf`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|---|---|
| entity | 29.7 [22.1–37.2] | 23.3 [16.9–30.5] | 35.0 | 0.941 | 54.5 / 23.5 (`ai`) |
| intent | 32.4 [25.5–40.0] | 29.6 [21.9–37.7] | 32.4 | 0.826 | 57.9 / 24.5 (`unintentional`) |
| timing | 35.9 [27.6–43.4] | 29.2 [17.2–43.6] | 16.3 | 0.692 | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 6.9%.

Per-class F1 % (gold support):

- **entity**: ai 7.0 (n=79), human 46.5 (n=51), other 16.3 (n=15)
- **intent**: intentional 34.8 (n=33), unintentional 33.9 (n=84), other 20.0 (n=28)
- **timing**: pre-deployment 25.0 (n=2), post-deployment 48.6 (n=132), other 13.9 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 34.1 / 29.1 | 38.8 / 34.0 | 27.1 / 16.6 |
| language=it | 60 | 23.3 / 13.1 | 23.3 / 23.3 | 48.3 / 37.7 |
| source=example | 34 | 32.4 / 22.3 | 35.3 / 31.5 | 29.4 / 18.3 |
| source=generated | 111 | 28.8 / 23.4 | 31.5 / 29.0 | 37.8 / 31.0 |
