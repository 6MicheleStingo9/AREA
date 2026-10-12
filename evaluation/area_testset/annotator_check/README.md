# Annotator check

A one-off estimate of the quality of the AREA training labels (`files/data/area_trainset/`): the same
protocol (two blind annotators, Claude Opus 5.5 subagents, and an adjudicator) applied to 60 risks of
this test set drawn at random (`python -m data_prep.area_trainset quality-sample`, seed 0), then scored
against the reviewed gold labels (`quality-score`). It was measured once, after the training labels were
final, and neither the rules nor the labels were changed after seeing it. These files are not used for
training.

| Axis | Accuracy % | Macro-F1 % |
|---|---|---|
| entity | 95.0 | 90.5 |
| intent | 85.0 | 75.9 |
| timing | 100.0 | 66.7 (no pre-deployment risk in the sample) |

The two annotators gave the same label on every axis of every risk, so the adjudicator had nothing to
settle. Of the errors, 3 are on entity (gold `ai` labelled `other` twice, gold `other` labelled `human`
once) and 9 on intent, 7 of them gold `other` labelled `unintentional`: the protocol uses `other` for
intent half as often as the gold (5 against 10 of the 60). For reference, the labels of the Gemini
pipeline reach 80.0 / 75.2 / 83.4 % accuracy on the whole test set.
