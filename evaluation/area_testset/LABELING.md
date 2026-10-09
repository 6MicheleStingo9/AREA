# Labeling guidelines — AREA causal test set

Gold labels for `risks.jsonl` follow the **MIT Causal Taxonomy of AI Risks** (Slattery et al.,
2025, CC BY 4.0), the same taxonomy as the MIT data used for training and for the baseline.
Each risk gets one value per axis, judged from its **title and text only**: the labels assigned
by the pipeline are not shown while labeling.

## Definitions (MIT, verbatim)

| Axis | Value | Definition |
|---|---|---|
| Entity | `ai` | The risk is caused by a decision or action made by an AI system |
| | `human` | The risk is caused by a decision or action made by humans |
| | `other` | The risk is caused by some other reason or is ambiguous |
| Intent | `intentional` | The risk occurs due to an expected outcome from pursuing a goal |
| | `unintentional` | The risk occurs due to an unexpected outcome from pursuing a goal |
| | `other` | The risk is presented as occurring without clearly specifying the intentionality |
| Timing | `pre-deployment` | The risk occurs before the AI is deployed |
| | `post-deployment` | The risk occurs after the AI model has been trained and deployed |
| | `other` | The risk is presented without a clearly specified time of occurrence |

## Decision rules

1. **Label what the text states or directly implies, not what is plausible.** If the text does
   not settle an axis, the value is `other`, as in the MIT data. Do not fill gaps with general
   knowledge of how such risks usually arise.
2. **Entity = whose decision or action produces the harm, as the text frames it.**
   - Framed around the system's outputs or behaviour (biased decisions, hallucinations, unsafe
     content) → `ai`, even if biased data is mentioned as a cause.
   - Framed around what people do: how they collect data, build, test or oversee the system,
     or how they use it (misuse, attacks, over-reliance) → `human`.
   - Both needed and neither dominant, or the cause not stated → `other`.
3. **Intent is about the harm, not the action.** Pursuing a goal that knowingly causes the harm
   (malicious use, attacks, deliberate trade-offs) → `intentional`. Harm as a side effect,
   error or failure → `unintentional`. Text that does not say → `other`.
4. **Timing = when the harm occurs, as the text frames it.** Harms of the system in use →
   `post-deployment`, even if introduced earlier (biased data showing up in outputs). Harms
   of the data collection, training or testing process itself → `pre-deployment`. Not stated,
   or explicitly spanning both → `other` (common for governance and regulatory risks).
5. Pick one value per axis and add a short note when the choice was hard; the notes are kept
   with the labels.

## Typical cases in the MIT training split

How the MIT annotators coded risks mentioning these themes (most frequent value, share of
the matching rows; `causal_clf.train.jsonl`, keyword match):

| Theme | Entity | Intent | Timing |
|---|---|---|---|
| Misuse, malicious actors (n=152) | human 76% | intentional 65% | post-deployment 80% |
| Attacks, adversarial inputs (n=131) | human 73% | intentional 75% | post-deployment 68% |
| Over-reliance, automation bias (n=23) | human 65% | unintentional 91% | post-deployment 78% |
| Bias, discrimination (n=115) | ai 59% | unintentional 61% | post-deployment 58% |
| Hallucinations, inaccuracy (n=70) | ai 57% | unintentional 50% | post-deployment 66% |
| Training data, datasets (n=103) | human 48% | unintentional 51% | pre-deployment 50% |
| Governance, regulation (n=52) | ai 46% | unintentional 44% | other 50% |

These are tendencies, not rules: the text of each risk decides.

## Workflow

Labels are proposed by Claude (Opus 5.5) with these rules, blind to the pipeline labels
(`proposals.jsonl`, with the axes in doubt and a short note), then reviewed by the author;
`labels.jsonl` records the final values and whether each proposal was changed.
