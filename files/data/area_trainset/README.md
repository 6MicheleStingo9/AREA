# AREA training risks

Risks written by AREA itself, labelled with the MIT Causal Taxonomy (entity, intent, timing), to
fine-tune Laya on how AREA frames its risks. The MIT training data teach the MIT annotators'
conventions on paper excerpts; the AREA test set (`evaluation/area_testset/`) follows
[LABELING.md](../../../evaluation/area_testset/LABELING.md) on AREA's own risk descriptions, and three
MIT-only fine-tuning runs could not learn that framing (e.g. a harm of the system in use is
post-deployment).

## Runs

[`data_prep/area_trainset.py`](../../../data_prep/area_trainset.py) defines 28 runs, `t01`–`t28`: each
describes a given AI system (28 systems, none of the kinds in the test set), in English and Italian
alternately, with the three simulated profiles in rotation. A run is the simulated questionnaire and
the domain analysis (Gemini 2.5 Flash); the causality step is skipped. `runs/<run>.json` keeps both
outputs; `risks.jsonl` has one row per risk (`collect`).

## Labels

No label in this folder was reviewed by a person (the author's choice). They come from a
three-annotator protocol with Claude subagents (Opus 5.5), each a fresh session given only the
rules of LABELING.md and the risks to label:

1. **Two independent annotators**, A and B, label every risk, blind to each other and to any other
   label in the repository, by reading each risk (no keyword rules). Each batch of runs goes to a new
   subagent per annotator: `annotations/a/<batch>.jsonl`, `annotations/b/<batch>.jsonl`, with the axes
   the annotator found hard (`doubt`) and a short note.
2. **Agreement** per axis, raw and as Cohen's kappa (`disagreements`). Both annotators are the same
   model with the same instructions, so their agreement measures how consistent the labelling is
   more than how correct; correctness is what the quality estimate (step 5) measures.
3. **An adjudicator** settles each disagreement: a fresh subagent sees the risk, the rules and both
   labels with their notes, and picks the final value with a reason (`annotations/adjudication/`).
4. **`labels.jsonl`**: the final value per axis and where it comes from (`agreed` or `adjudicated`)
   (`merge`).
5. **Quality estimate**, once, after the labelling: the annotator protocol applied to 60 random risks
   of the test set, scored against its reviewed gold labels (`quality-sample`, `quality-score`). It is
   a measurement only: rules and labels are not changed after seeing it.

```bash
python -m data_prep.area_trainset generate        # calls the LLM; resumable, stops at an exhausted quota
python -m data_prep.area_trainset collect
python -m data_prep.area_trainset batches         # unlabelled risks, a few runs per batch, for the annotators
python -m data_prep.area_trainset disagreements   # agreement, kappa, the disputed risks for the adjudicator
python -m data_prep.area_trainset merge           # labels.jsonl
```

The risks are derived from Gemini outputs on simulated questionnaires; they describe no real system.
