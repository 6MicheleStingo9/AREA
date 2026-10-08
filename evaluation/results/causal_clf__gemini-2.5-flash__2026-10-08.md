# Causal classification — gemini-2.5-flash baseline

Eval: `files/data/processed/causal_clf.eval.jsonl` (160 risks, frozen split). Run 2026-10-08 · batch 20 · repeats 2 · 16 calls, 29.6 s per call · commit `079b63d`.

| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | Majority class: acc / macro-F1 % |
|---|---|---|---|
| entity | 72.5 [65.0–79.4] | 58.6 [51.3–66.1] | 38.8 / 18.6 (`ai`) |
| intent | 62.5 [55.0–70.0] | 52.4 [45.3–59.2] | 40.6 / 19.3 (`unintentional`) |
| timing | 71.9 [65.6–78.8] | 54.1 [45.3–62.1] | 65.0 / 26.3 (`post-deployment`) |

All three axes correct: 40.6%.

Per-class F1 %:

- **entity**: ai 80.0 (n=62), human 79.7 (n=66), other 16.2 (n=32)
- **intent**: intentional 77.2 (n=57), unintentional 66.7 (n=65), other 13.3 (n=38)
- **timing**: pre-deployment 58.2 (n=18), post-deployment 85.2 (n=104), other 19.0 (n=38)

Agreement between repeated runs %: entity 93.8, intent 93.1, timing 90.0
