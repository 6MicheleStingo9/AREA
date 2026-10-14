# The MIT taxonomies

Kindynos assesses AI risks with the two taxonomies of the [MIT AI Risk Repository](https://airisk.mit.edu/)
([Slattery et al., 2024](#reference)): the Domain Taxonomy says what kind of harm a risk is, the Causal
Taxonomy says how it comes about.

## Domain Taxonomy

Seven domains and 24 subdomains. Each question of the Kindynos questionnaire covers one subdomain and has
its code (question 1.1 covers subdomain 1.1), and the domain analysis writes the risks of each subdomain.

| Domain | Subdomains |
|---|---|
| 1 Discrimination & Toxicity | 1.1 Unfair discrimination and misrepresentation<br>1.2 Exposure to toxic content<br>1.3 Unequal performance across groups |
| 2 Privacy & Security | 2.1 Compromise of privacy by leaking or correctly inferring sensitive information<br>2.2 AI system security vulnerabilities and attacks |
| 3 Misinformation | 3.1 False or misleading information<br>3.2 Pollution of information ecosystem and loss of consensus reality |
| 4 Malicious Actors & Misuse | 4.1 Disinformation, surveillance, and influence at scale<br>4.2 Cyberattacks, weapon development or use, and mass harm<br>4.3 Fraud, scams, and targeted manipulation |
| 5 Human-Computer Interaction | 5.1 Overreliance and unsafe use<br>5.2 Loss of human agency and autonomy |
| 6 Socioeconomic & Environmental | 6.1 Power centralization and unfair distribution of benefits<br>6.2 Increased inequality and decline in employment quality<br>6.3 Economic and cultural devaluation of human effort<br>6.4 Competitive dynamics<br>6.5 Governance failure<br>6.6 Environmental harm |
| 7 AI System Safety, Failures, & Limitations | 7.1 AI pursuing its own goals in conflict with human goals or values<br>7.2 AI possessing dangerous capabilities<br>7.3 Lack of capability or robustness<br>7.4 Lack of transparency or interpretability<br>7.5 AI welfare and rights<br>7.6 Multi-agent risks |

**Example.** Question 1.1, "What user data or attributes are collected or used by the system to provide
services, make decisions, or generate outputs?", covers *1.1 Unfair discrimination and misrepresentation*:
the answer shows whether the system could treat groups of people unfairly because of the data it uses.

## Causal Taxonomy

Three axes, each with three values. The definitions are the MIT ones, verbatim:

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

Kindynos applies them with a few decision rules, written for its own risk texts
([LABELING.md](../evaluation/area_testset/LABELING.md)): label what the text states, not what is plausible;
the entity is whoever's decision or action produces the harm, as the text frames it; the intent is about
the harm, not the action; the timing is when the harm occurs, so the harms of a system in use are
post-deployment even when they were introduced earlier.

**Examples.**

- *"The system could be misused for generating convincing phishing messages, executing targeted scams, or
  engaging in manipulative conversational tactics."* Entity `human` (people misuse the system), intent
  `intentional` (the harm is their goal), timing `post-deployment` (it happens with the system in use).
- *"The system's outputs are biased against some groups, because its training data under-represent
  them."* Entity `ai` (the text is about the system's outputs), intent `unintentional` (a side effect),
  timing `post-deployment` (the harm occurs in use, even if the bias comes from training).

## Reference

Slattery, P., Saeri, A. K., Grundy, E. A. C., Graham, J., Noetel, M., Uuk, R., Dao, J., Pour, S.,
Casper, S., & Thompson, N. (2024). *The AI Risk Repository: A Comprehensive Meta-Review, Database, and
Taxonomy of Risks from Artificial Intelligence.* https://doi.org/10.48550/arXiv.2408.12622

Kindynos uses version 4 of the repository (December 2025), included in [files/data/](../files/data/README.md)
under CC BY 4.0.
