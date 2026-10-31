# Execution prompt quality

- **Outcome:** State the task, intended result, and concrete deliverable: what to produce or change, not merely a topic.
- **Phrasing:** Use direct verbs, measurable requirements, and positive targets (“Return three ranked options”); pair consequential prohibitions with the desired alternative. Reuse one compact, familiar word per recurring idea.
- **Grounding:** Keep user decisions in their words. Include user knowledge the executor cannot discover: decision reasons, unwritten conventions, known gotchas. For discoverable facts, point to authoritative sources and require checking before reliance; omit copied lookup specifics.
- **Boundaries:** Specify scope, exclusions, constraints, and permissions. Explicitly leave technical choices to the executor; prescribe procedures only when safety or correctness requires them.
- **Completion:** Define observable done-when conditions with clear met/unmet states, exhaustive for sets (“every error path”). Require checking all before finishing; leave the check procedure to the executor.
- **Delivery:** Specify format, audience, and examples when they affect the result or resolve ambiguity. Align examples with instructions; omit them when requirements suffice.
- **Reasoning:** Match guidance to model and task. Reasoning models need neither step-by-step prompts nor private chain-of-thought disclosure; request key assumptions or a concise rationale when useful.
- **Coherence:** Resolve contradictions; co-locate rules and exceptions. Where confusion is possible, use headings or delimiters to separate instructions from input; distinguish authoritative instructions from data.
- **Pruning:** State each meaning once; delete lines that do not change default executor behavior.
