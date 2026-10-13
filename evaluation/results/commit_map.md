# Commit map

The history of this repository was rewritten twice to replace the author and committer email of some
commits:

- on 2026-10-12, the commits of `rework/area` not yet in `main`;
- on 2026-10-13, the commits of `main` after GitHub's initial commit, and with them every later commit.

Their content (trees), names and dates did not change; nor did their messages, except for the commit
hashes a few of them cite, updated to the rewritten ones. Results files, notes and earlier messages may
cite an earlier hash: this table gives the current one, oldest commit first.

| Earlier | Current | Subject |
|---|---|---|
| `f4d8aae` | `3a53306` | First commit |
| `8d5b836` | `de087d1` | Fix typo in README.md: corrected "Refernces" to "References" |
| `283a6b2` | `f130c9f` | Fix path in README.md: updated UI launch script reference |
| `7329b5e` | `d8d6c6d` | feat: Add new AI risk report metadata and remove outdated reports |
| `344022a` | `a57b6e1` | Fix typo in answers_20251227_160418.json: corrected "he" to "The" |
| `5e4dc9f`, `3d097d4` | `660a6e0` | fix: make the pipeline portable and resilient |
| `c9702a5`, `1567a13` | `c62226d` | feat(report): make the HTML report self-contained |
| `f7d7fbc`, `c9a60d7` | `bb9fc31` | feat(ui): replace the Streamlit UI with a FastAPI + htmx questionnaire |
| `77434ee`, `f4eca50` | `e41904c` | build: add a single-container Docker setup |
| `e4424a1`, `27ced4c` | `d6b52c1` | docs: document the FastAPI UI and the Docker setup |
| `cc4474c`, `c6309a3` | `b74eb69` | chore: ignore local plans and Claude settings; drop the langgraph.json rule |
| `4c1e822`, `b9a3d7d` | `d6ea3b7` | fix(ui): lost Next click, untranslated pages, endless no-JS progress |
| `08c13a1`, `811512c` | `69ed1c8` | fix(report): readable dark mode and translated ZIP messages |
| `f1773f0`, `48fdfe0` | `be3cf57` | fix(domain): keep the severity rationale written with the severity |
| `75fe80c`, `05763e2` | `9401b5d` | fix(deps): pin langgraph-prebuilt to 1.0.8 |
| `4153650`, `4fba78e` | `3cbb4da` | fix(docker): run the container as the host user |
| `c9b8d2b`, `e52103f` | `989688d` | docs: run standalone agents as modules; add .env.example |
| `45700d7`, `b0f6e90` | `8aaa034` | chore: ignore __pycache__ directories everywhere |
| `6c3e2e7`, `c60edea` | `cec8a0c` | fix(ui): make the questionnaire usable without JS |
| `784ef1a`, `509ecf5` | `f1e8e1b` | fix(quiz): compare option indices in option_index_in on checkboxes |
| `9002248`, `07d39a0` | `51eb57c` | fix(agents): record each error once in the graph state |
| `50647a8`, `cd7c18e` | `a99c68b` | fix(report): AA contrast for the subdomain badges |
| `92d649e`, `53b2a33` | `ef8b7e9` | test: add pytest unit tests for the quiz logic and the agent state |
| `e067e9f`, `33ac8d3` | `e04924d` | feat(data): add the MIT AI Risk Repository v4 (CC BY 4.0) |
| `25782a4`, `5157ff1` | `8ff131f` | feat(data): add the dataset extraction script |
| `ca29f22`, `d9067e0` | `49f197e` | fix(data): split by risk category to avoid train/eval leakage |
| `f50b29b`, `f2e75c4` | `79afbe6` | data: extract the processed MIT datasets (frozen eval split) |
| `d7b5db2`, `cd58e20` | `839b432` | feat(evaluation): Gemini baseline for the causal classification |
| `4c4e1d9`, `0bacad4` | `e2516e2` | fix(llm): make apply_retry() the only retry layer |
| `e77910e`, `1b34846` | `56467d3` | feat(evaluation): checkpoint and resume the causal baseline |
| `079b63d`, `441360c` | `fb02581` | docs(readme): note the Gemini free tier daily quota |
| `d0735e2`, `d105c57` | `2712605` | results: Gemini 2.5 Flash baseline on the causal classification eval |
| `afe6b8a`, `638fb37` | `e384a72` | fix(llm): JSON mode for the questionnaire generator, timeout, longer retries |
| `197ad3f`, `408c189` | `14359c6` | feat(evaluation): in-distribution test set of AREA risks |
| `eb72546`, `911327a` | `e75935c` | feat(evaluation): gold labels and scoring for the AREA test set |
| `34c67e0`, `aabce14` | `8537859` | results: Gemini pipeline labels on the AREA test set |
| `bcd1cee`, `f5dd7ab` | `744a9fc` | labels: harmonize near-duplicate AREA risks |
| `9381e60`, `64acdb9` | `715a1ea` | results: Gemini pipeline labels on the harmonized AREA gold |
| `902e6bf`, `bdeb3d3` | `4b2b594` | feat(training): fine-tune and evaluate Laya-multilingual on the causal taxonomy |
| `de5c5de`, `a27b314` | `24fce88` | results: Laya-multilingual zero-shot on both causal test sets |
| `b517d75`, `b282080` | `572fdd2` | feat(evaluation): side-by-side comparison of the causal classifiers |
| `a4a7806`, `8eafcf0` | `1202f9b` | results: fine-tuned Laya-multilingual on both causal test sets |
| `878942c`, `a39d54e` | `5cc3cac` | feat(training): validation split, calibration on it, variant selection |
| `430957d`, `8d8e701` | `08846e1` | results: second Laya fine-tuning iteration on both causal test sets |
| `50256c6`, `c500034` | `99810ff` | feat(training): subdomain in Laya's input, calibration-aware selection |
| `a159903`, `94e05f2` | `d81c9c1` | results: third Laya iteration (subdomain in the input) on both test sets |
| `1f0e6b1`, `ed2b2d3` | `7d98097` | feat(data): AREA training runs and a labelling protocol with subagents |
| `4e9f6ee`, `e24d8d0` | `7975b40` | fix(questionnaire): parse replies in content blocks, keep the JSON valid |
| `e307c46`, `f38d1d7` | `01315b9` | feat(training): train on AREA's own risks, select and calibrate on AREA runs |
| `04f285c`, `138a498` | `91909c0` | data: first 16 AREA training runs, labelled (265 risks) |
| `8163eae` | `7c127db` | docs: map the original commit hashes of rework/area to the rewritten ones |
| `3038c69` | `7248f5f` | data: AREA training runs t17-t28 (all 28 runs, 466 risks) |
| `b576a26` | `7b76e12` | data: labels of all 466 AREA training risks, and their quality estimate |
| `b1b2bd1` | `2017fc9` | results: fourth Laya iteration, trained on AREA's own risks, beats the criterion |
| `d3c0656` | `d6c9c4e` | causality: Laya labels the causality in the pipeline |
| `d63396f` | `9cc16c6` | rename: the project is now Kindynos (formerly AREA) |
| `10af843` | `5d9c4c9` | notebook: clone the renamed repository into kindynos/ |
| `63767ab` | `c5a1f65` | brand: the Kindynos logo, mascot and social preview |
| `81853d5` | `6ecb761` | brand: the logo in the web interface and in the report |
| `547d50c` | `a8b150e` | publish: build the Hugging Face model and dataset repositories |
| `0f9cc51` | `a58770d` | notebook: a commented Kaggle notebook for laya-kindynos-causal |
| `e83837c` | `e76e3b0` | causality: without a local checkpoint, use the published model |
