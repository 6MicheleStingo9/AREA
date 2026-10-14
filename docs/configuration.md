# Configuration

Kindynos reads its settings from environment variables or from a `.env` file in the project root, for
which `.env.example` is a template. Only `GOOGLE_API_KEY` is required.

| Variable | Default | What it does |
|---|---|---|
| `GOOGLE_API_KEY` | none, required | the Google Gemini API key, from [Google AI Studio](https://aistudio.google.com/) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | the Gemini model of the domain analysis and of the report summary |
| `CAUSALITY_BACKEND` | `laya` | who labels the causes: `laya`, the local model, or `llm`, Gemini |
| `LAYA_MODEL` | see [below](#the-causal-model) | the directory or Hugging Face id of the Laya model |
| `LAYA_REVISION` | `v1.0` for the published model | the revision of a model on Hugging Face |
| `LAYA_REVIEW_THRESHOLD` | `0.9` | labels below this confidence are flagged for review |
| `LOG_LEVEL` | `INFO` | how much Kindynos logs: `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL` |
| `UID`, `GID` | `1000` | with Docker, the user the container runs as |

## Gemini and its quota

Each assessment makes 2 requests to Gemini, for the domain analysis and the report summary, or 3 with
`CAUSALITY_BACKEND=llm`. The free tier of the Gemini API has a daily quota per model (20 requests for
`gemini-2.5-flash` as of October 2026), so it allows about ten assessments a day; past the quota, requests
fail with `429 RESOURCE_EXHAUSTED` until it resets. Transient errors, such as "high demand" 503s, are
retried for about a minute, and so is a request that gets no reply within 3 minutes.

## The causal model

The causal analysis uses laya-kindynos-causal, on the CPU and without API calls
([training](../training/README.md)).

- **Which model.** `LAYA_MODEL` when set; otherwise the local checkpoint `training/checkpoints/laya-causal-v4`
  when present (it comes from training and is not in the repository); otherwise the published
  [laya-kindynos-causal](https://huggingface.co/MicheleStingo/laya-kindynos-causal), revision `v1.0`,
  downloaded from Hugging Face on first use (615 MB) and cached.
- **Speed.** The model loads once per process (6–9 s) and labels a risk in about 2 s on a laptop CPU
  (i7-1255U, 1.4–2.6 s): under a minute for an assessment of 20 risks, in Docker too.
- **Review flag.** Laya writes no text: in the report each label comes with the MIT definition of its
  value and Laya's confidence, the calibrated probability of that value. Labels below 90% confidence are
  marked ⚠, with the next most likely value. The threshold was chosen on Kindynos runs held out from
  training (the test set was not used): there, the labels below it were 59% correct, the others 94%. On
  the test set, measured once afterwards, 4.6% of the labels are flagged and half of them are wrong,
  against 11% of the others. Most errors are confident ones, so the flag points out doubtful labels but
  does not catch every mistake.
- **Same labels as evaluated.** On the 145 test risks, the causality step gives all 435 labels scored in
  `evaluation/results/` (computed on a GPU), with probabilities within 0.01.
- **Without the model.** If the model or its packages are missing, the default backend stops the run with
  an error that says how to fix it, and the web interface already logs the problem when it starts: it does
  not switch to the LLM on its own. `CAUSALITY_BACKEND=llm` has the LLM label the causes, with rationales it
  writes, at the cost of one more request per assessment.

## Docker

- The image, about 2 GB with CPU-only PyTorch, includes SWI-Prolog and every package, but not the causal
  model.
- `./files` is mounted in the container, so answers, analyses, reports and the state of the analyses stay on
  the host. The published model is cached in `files/.cache/huggingface`.
- `./training` is mounted read-only, so the container uses a local checkpoint in
  `training/checkpoints/laya-causal-v4` when there is one.
- The container runs as UID/GID 1000, so the files it writes stay editable on the host; if your user has
  different ids, set `UID` and `GID` in `.env` (for example `UID=1001`).
