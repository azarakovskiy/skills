# Model selection: evidence and scope

2026-10-10

## Decision

Every recommendation includes a **Lightweight / Standard / Frontier category, effort, and concise task-grounded reason**; users map the categories to their preconfigured lineup. Do **not** add the research-derived evidence-precedence sentence to runtime instructions: the controlled probes showed no additional selection benefit. Revisit it if a real failure demonstrates that the existing behavior ignores relevant task evidence.

## Scope and existing coverage

`prompt-me` recommends generic categories, not specific model names or lineup mappings; users map the categories to their own preconfigured lineup. Model discovery and mapping lookup are out of scope. The question is whether research supports a small improvement to that advice, not a replacement selection system. This note is a research record, separate from runtime instructions.

The existing heuristics already distinguish routine work and settled-plan execution from ordinary judgment, difficult planning, ambiguity, and costly mistakes. They also choose effort independently, distinguish advisory headroom from required capabilities, and ground context needs in material that must be held together. The planner/executor distinction is therefore **already covered**, not a research-discovered omission. Much of the provider guidance below supports these existing choices rather than requiring new wording.

## Vendor advice

- **Evaluate against the actual quality bar.** [OpenAI's model-selection guide](https://developers.openai.com/api/docs/guides/model-selection) calls its recommendations a starting point: compare models and reasoning settings on the same inputs, then keep the lightest setting meeting the quality bar. Frequency, latency, output use, and quality requirements affect that choice. This is workflow-calibration advice, not a requirement to benchmark each incoming prompt.
- **Capability, speed, cost, and effort are separate considerations.** [Anthropic's selection guide](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model) offers efficiency-first and capability-first starting points, followed by evaluation using actual prompts, data, and edge cases. Its [effort documentation](https://platform.claude.com/docs/en/build-with-claude/effort) describes effort as a behavioral signal, not a strict token budget; it can affect thinking, text, and tool calls. Generic effort labels should not promise identical behavior across providers.
- **Reasoning needs depend on the task.** [Google's thinking guidance](https://ai.google.dev/gemini-api/docs/generate-content/thinking#tasks) distinguishes straightforward retrieval/classification, ordinary comparisons, and demanding math or coding. This broadly supports complexity-based effort selection. Its specific controls and recommendations remain provider-specific, not a universal mapping from task names to settings.

These are first-party operating recommendations, not independent comparisons establishing a universally best model or effort level.

## Empirical findings and limits

**Task-distribution match matters.** [Ong et al., RouteLLM](https://arxiv.org/html/2406.18665v4) found that routers trained only on conversational preference data performed near random on MMLU and GSM8K; task-aligned augmentation improved routing. Some transfer across unseen model pairs succeeded on MT Bench. The evidence concerns learned, two-model routers on benchmark distributions. It supports caution about transferring average rankings across tasks, not confidence that a conversational advisor can select correctly from a task label alone.

**More computation is not an unconditional improvement.** [Snell et al.](https://arxiv.org/html/2408.03314v1) studied specialized mathematical reasoning with revision and verifier-guided search. Effective compute allocation depended on the problem and base model. Increasing beam-search budgets degraded performance on easier problems, while tested methods made little progress on the hardest problems. These are findings about particular search/revision strategies on MATH, not proof that increasing a current provider's effort setting usually harms easy tasks. Their difficulty estimation also used substantial computation; it is not a free procedure for this skill.

## Inferred application to prompt-me

A plausible small candidate is: **let already-available, trustworthy performance evidence matching the task and success criterion override a generic tier recommendation**. A broad label such as “coding,” an unrelated leaderboard, or an unsupported reputation is not that evidence. Without a close match, retain the familiar task/effort/capability heuristics and reliability margin.

This inference adds an evidence-precedence rule, not another classification scheme. Requiring fresh benchmarks or a model inventory per prompt would turn brief preparation into calibration work and contradict the confirmed familiar-lineup scope. Vendor catalogs would add maintenance and invite stale mappings. Loading this research into runtime context would add reading without giving most requests another useful decision; keep only behaviorally useful guidance there.

Provider documents and papers do **not** prove that inserting this candidate sentence improves `prompt-me`. Routing and math studies are not benchmarks of this skill. The comparison below checks recommendation behavior, not whether the recommended models complete downstream tasks better.

## Earlier named-model implementation: behavioral comparison

Used fresh, stateless OMP completions with the same `default` selector (session model: `openai-codex/gpt-6-astra`). Each run received only its own complete skill package and the scenario. Criteria were fixed before generation; output pairs were anonymously labeled for same-model grading. Raw outputs remained in session memory. This was a small development smoke comparison, not a statistical study or human-confirmed promotion.

The six existing prompts were preserved; three rubrics were updated for the then-interpreted concise named-model output contract, and one familiar-lineup scenario was added. All seven repository scenarios and four exploratory probes met that implementation's behavioral criteria, not a verification of the corrected category output. The probes covered matched task evidence versus role tiers, an unrelated leaderboard, a demonstrated effort ceiling, and image capability versus a stronger text-only model.

Model-advice word counts, excluding Markdown list markers and the Models label:

| Scenario | Before named-model change | Earlier named-model implementation |
| --- | ---: | ---: |
| Settled mechanical edit; user asks about maximum effort | 84 | 36 |
| Difficult protocol analysis followed by checked copying | 140 | 48 |
| Familiar lineup for ordinary endpoint work | 61 | 7 |

The research ablation added only the candidate sentence to the earlier named-model package in memory. Both arms met all four probe rubrics (12 criteria each), so the sentence was dropped. This does not establish universal equivalence; it supplies no observed benefit worth the extra runtime instruction.

`python3 scripts/evals.py` passed; all seven local package references resolved. The stored `comparison` was reset to `null` because the rubric changed, so the reporter correctly warns that promotion evidence is missing. No new human-confirmed score was fabricated; a formal promotion remains separate.

## Category-only correction

The user clarified that the preconfigured lineup explains why advice can stay short; recommendations must still use **Lightweight / Standard / Frontier**, with no specific model names or lineup mapping.

Reran the seven repository scenarios and one configured-lineup handoff probe using fresh OMP completions with the same default selector. All five model-advice/handoff scenarios passed. Both the named-lineup brief and handoff used **Standard** without echoing supplied model names; the handoff retained the **Required** image capability.

The broader smoke run passed seven of eight scenarios (32 of 33 criteria). Its remaining finding concerned choosing separate passes for every mobile platform before inspection establishes distinct working sets. That split-planning behavior is outside this naming correction; the smart-zone instructions were left unchanged.

Structural validation passed with the expected missing-comparison warning. No formal promotion score was recorded.

## Mandatory effort and reason

After making effort and a concise reason mandatory in both briefs and handoffs, reran the four affected repository scenarios and the configured-lineup handoff probe using the same stateless OMP setup. All five scenarios passed all 21 criteria, covering ordinary work without an explicit effort question, different needs across steps, and reusable prompts with required image capability. Structural validation passed with the expected missing-comparison warning. This focused run did not retest the broader split-planning finding above.
