# Causal classification on AREA risks — pipeline labels vs gold

Test set: `evaluation/area_testset/risks.jsonl` (145 risks: 85 EN, 60 IT); gold: `evaluation/area_testset/labels.jsonl` (reviewed by hand, see LABELING.md). Pipeline model by source: example: unknown; generated: gemini-2.5-flash. Run 2026-10-09 · commit `eb72546`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|
| entity | 80.0 [73.1–86.2] | 63.2 [53.8–73.2] | 54.5 / 23.5 (`ai`) |
| intent | 71.0 [63.4–78.6] | 53.3 [48.2–57.6] | 53.1 / 23.1 (`unintentional`) |
| timing | 83.4 [77.2–89.0] | 49.6 [35.3–62.6] | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 60.0%.

Per-class F1 % (gold support):

- **entity**: ai 85.3 (n=79), human 82.0 (n=51), other 22.2 (n=15)
- **intent**: intentional 79.4 (n=35), unintentional 80.4 (n=77), other 0.0 (n=33)
- **timing**: pre-deployment 16.0 (n=2), post-deployment 92.8 (n=132), other 40.0 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 83.5 / 70.1 | 76.5 / 57.7 | 91.8 / 54.3 |
| language=it | 60 | 75.0 / 53.1 | 63.3 / 46.9 | 71.7 / 35.7 |
| source=example | 34 | 91.2 / 77.1 | 79.4 / 58.6 | 97.1 / 59.5 |
| source=generated | 111 | 76.6 / 58.5 | 68.5 / 51.0 | 79.3 / 42.3 |

Gold labels changed from the proposals they were reviewed from: entity 6.9%, intent 6.9%, timing 0.0%.
