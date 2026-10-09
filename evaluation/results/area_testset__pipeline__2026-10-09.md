# Causal classification on AREA risks — pipeline labels vs gold

Test set: `evaluation/area_testset/risks.jsonl` (145 risks: 85 EN, 60 IT); gold: `evaluation/area_testset/labels.jsonl` (reviewed by hand, see LABELING.md). Pipeline model by source: example: unknown; generated: gemini-2.5-flash. Run 2026-10-09 · commit `bcd1cee`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | Majority class (MIT train): acc / macro-F1 % |
|---|---|---|---|
| entity | 80.0 [73.1–86.2] | 63.2 [53.8–73.3] | 54.5 / 23.5 (`ai`) |
| intent | 75.2 [68.3–82.1] | 55.2 [50.4–59.1] | 57.9 / 24.5 (`unintentional`) |
| timing | 83.4 [77.2–89.0] | 49.6 [35.3–62.6] | 91.0 / 31.8 (`post-deployment`) |

All three axes correct: 59.3%.

Per-class F1 % (gold support):

- **entity**: ai 85.3 (n=79), human 82.0 (n=51), other 22.2 (n=15)
- **intent**: intentional 81.8 (n=33), unintentional 83.7 (n=84), other 0.0 (n=28)
- **timing**: pre-deployment 16.0 (n=2), post-deployment 92.8 (n=132), other 40.0 (n=11)

| Subset | n | entity acc / macro-F1 % | intent acc / macro-F1 % | timing acc / macro-F1 % |
|---|---|---|---|---|
| language=en | 85 | 83.5 / 69.4 | 76.5 / 58.3 | 91.8 / 54.3 |
| language=it | 60 | 75.0 / 52.6 | 73.3 / 50.7 | 71.7 / 35.7 |
| source=example | 34 | 91.2 / 77.1 | 73.5 / 57.4 | 97.1 / 59.5 |
| source=generated | 111 | 76.6 / 58.5 | 75.7 / 53.6 | 79.3 / 42.3 |

Gold labels that differ from the proposals they were reviewed from: entity 8.3%, intent 9.0%, timing 0.0%. Harmonized after the review (near-duplicate risks, see LABELING.md): entity 2, intent 15, timing 0.
