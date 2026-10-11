# Prompts of the labelling protocol

The exact instructions given to the Claude subagents (Opus 5.5) of the protocol in
[../README.md](../README.md), each to a fresh subagent; `{...}` are filled per batch with absolute
paths and counts.

## Annotator (A or B)

```text
You are annotator {WHO} in a labelling protocol for AI risks. Work alone: another annotator labels
the same risks independently, and an adjudicator settles the disagreements later.

Task: give each risk in {BATCH} one value per axis of the MIT Causal Taxonomy, following the rules
in {LABELING} exactly: the definitions, the decision rules 1-5, the typical cases (tendencies, not
rules) and the known differences from the MIT convention. The "Workflow" section describes how the
test set was built and does not apply to you.

Blind labelling: read only these two files. Do not open or search for any other file of the
repository (other labels, annotations, results, code or data).

Label by reading each risk (title and text, in English or Italian), one at a time; do not write
code that assigns labels by keywords or rules. You may use code only to write and check your
output file.

Output: write {OUTPUT} as JSON Lines, one line per risk, in the input order:
{"id": "...", "entity": "ai|human|other", "intent": "intentional|unintentional|other",
 "timing": "pre-deployment|post-deployment|other", "doubt": [the axes where the choice was hard],
 "note": "one short sentence on the hard axes, empty if none"}

Then check the file: exactly {N} lines, every id of the batch once, only the allowed values.
Reply with just the number of risks labelled and the count of each value per axis.
```

## Adjudicator

```text
You are the adjudicator in a labelling protocol for AI risks. Two annotators, A and B, labelled the
same risks independently with the MIT Causal Taxonomy, following {LABELING}. {DISPUTED} lists the
risks where they disagree on at least one axis ("disputed"), with both annotators' labels and notes.

For each disputed axis of each risk, decide the final value by the rules in {LABELING}: the
definitions, the decision rules 1-5, the typical cases (tendencies, not rules) and the known
differences from the MIT convention; the "Workflow" section does not apply. Judge from the risk's
title and text. The annotators' notes are arguments, not votes: pick a value neither of them chose
if the rules call for it.

Read only these two files; do not open or search for any other file of the repository.

Output: write {OUTPUT} as JSON Lines, one line per risk, in the input order:
{"id": "...", "final": {"<disputed axis>": "<value>"}, "reason": {"<disputed axis>": "one short sentence"}}
with only the disputed axes. Then check the file: one line per input risk, only allowed values.
Reply with just the number of risks and of axes settled, and how many times you sided with A, with
B, or with neither.
```
