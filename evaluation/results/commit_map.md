# Commit map of the rework/area branch

On 2026-10-12 the history of `rework/area` was rewritten to replace the author and committer
email of its commits; their content (trees) did not change. Results files, notes and earlier messages
may cite the original hashes: this table maps each to the rewritten commit.

| Original | Rewritten | Subject |
|---|---|---|
| `5e4dc9f` | `3d097d4` | fix: make the pipeline portable and resilient |
| `c9702a5` | `1567a13` | feat(report): make the HTML report self-contained |
| `f7d7fbc` | `c9a60d7` | feat(ui): replace the Streamlit UI with a FastAPI + htmx questionnaire |
| `77434ee` | `f4eca50` | build: add a single-container Docker setup |
| `e4424a1` | `27ced4c` | docs: document the FastAPI UI and the Docker setup |
| `cc4474c` | `c6309a3` | chore: ignore local plans and Claude settings; drop the langgraph.json rule |
| `4c1e822` | `b9a3d7d` | fix(ui): lost Next click, untranslated pages, endless no-JS progress |
| `08c13a1` | `811512c` | fix(report): readable dark mode and translated ZIP messages |
| `f1773f0` | `48fdfe0` | fix(domain): keep the severity rationale written with the severity |
| `75fe80c` | `05763e2` | fix(deps): pin langgraph-prebuilt to 1.0.8 |
| `4153650` | `4fba78e` | fix(docker): run the container as the host user |
| `c9b8d2b` | `e52103f` | docs: run standalone agents as modules; add .env.example |
| `45700d7` | `b0f6e90` | chore: ignore __pycache__ directories everywhere |
| `6c3e2e7` | `c60edea` | fix(ui): make the questionnaire usable without JS |
| `784ef1a` | `509ecf5` | fix(quiz): compare option indices in option_index_in on checkboxes |
| `9002248` | `07d39a0` | fix(agents): record each error once in the graph state |
| `50647a8` | `cd7c18e` | fix(report): AA contrast for the subdomain badges |
| `92d649e` | `53b2a33` | test: add pytest unit tests for the quiz logic and the agent state |
| `e067e9f` | `33ac8d3` | feat(data): add the MIT AI Risk Repository v4 (CC BY 4.0) |
| `25782a4` | `5157ff1` | feat(data): add the dataset extraction script |
| `ca29f22` | `d9067e0` | fix(data): split by risk category to avoid train/eval leakage |
| `f50b29b` | `f2e75c4` | data: extract the processed MIT datasets (frozen eval split) |
| `d7b5db2` | `cd58e20` | feat(evaluation): Gemini baseline for the causal classification |
| `4c4e1d9` | `0bacad4` | fix(llm): make apply_retry() the only retry layer |
| `e77910e` | `1b34846` | feat(evaluation): checkpoint and resume the causal baseline |
| `079b63d` | `441360c` | docs(readme): note the Gemini free tier daily quota |
| `d0735e2` | `d105c57` | results: Gemini 2.5 Flash baseline on the causal classification eval |
| `afe6b8a` | `638fb37` | fix(llm): JSON mode for the questionnaire generator, timeout, longer retries |
| `197ad3f` | `408c189` | feat(evaluation): in-distribution test set of AREA risks |
| `eb72546` | `911327a` | feat(evaluation): gold labels and scoring for the AREA test set |
| `34c67e0` | `aabce14` | results: Gemini pipeline labels on the AREA test set |
| `bcd1cee` | `f5dd7ab` | labels: harmonize near-duplicate AREA risks |
| `9381e60` | `64acdb9` | results: Gemini pipeline labels on the harmonized AREA gold |
| `902e6bf` | `bdeb3d3` | feat(training): fine-tune and evaluate Laya-multilingual on the causal taxonomy |
| `de5c5de` | `a27b314` | results: Laya-multilingual zero-shot on both causal test sets |
| `b517d75` | `b282080` | feat(evaluation): side-by-side comparison of the causal classifiers |
| `a4a7806` | `8eafcf0` | results: fine-tuned Laya-multilingual on both causal test sets |
| `878942c` | `a39d54e` | feat(training): validation split, calibration on it, variant selection |
| `430957d` | `8d8e701` | results: second Laya fine-tuning iteration on both causal test sets |
| `50256c6` | `c500034` | feat(training): subdomain in Laya's input, calibration-aware selection |
| `a159903` | `94e05f2` | results: third Laya iteration (subdomain in the input) on both test sets |
| `1f0e6b1` | `ed2b2d3` | feat(data): AREA training runs and a labelling protocol with subagents |
| `4e9f6ee` | `e24d8d0` | fix(questionnaire): parse replies in content blocks, keep the JSON valid |
| `e307c46` | `f38d1d7` | feat(training): train on AREA's own risks, select and calibrate on AREA runs |
| `04f285c` | `138a498` | data: first 16 AREA training runs, labelled (265 risks) |
