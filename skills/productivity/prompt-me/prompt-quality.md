# Execution prompt quality

- **Outcome:** State the task, intended result, and concrete deliverable: what the executor should produce or change, not merely the topic.
- **Phrasing:** Use direct verbs and measurable requirements. State positive target behavior (“Return three ranked options”); pair consequential prohibitions with the desired alternative. Name a recurring idea with one compact, familiar word and reuse that word instead of restating the idea.
- **Grounding:** Carry the user's decisions in their own words. Spell out what the user knows and the executor cannot find by looking: the reason behind a decision, an unwritten convention, a known gotcha. Point to authoritative sources for discoverable facts and require checking them before reliance, rather than copying looked-up specifics.
- **Boundaries:** Specify scope, exclusions, constraints, and permissions. Leave technical choices to the executor and say so; prescribe a procedure only when safety or correctness requires it.
- **Completion:** Define observable done-when conditions the executor can tell met from unmet, exhaustive where the work covers a set (“every error path”, not “the error paths”). Require checking the result against them before finishing; leave the check procedure to the executor.
- **Delivery:** Specify format, audience, and examples when they change the result or resolve ambiguity. Keep examples consistent with instructions; omit them when the requirements suffice.
- **Reasoning:** Match guidance to the model and task. Reasoning models need no step-by-step prompting or private chain-of-thought disclosure; request key assumptions or a concise rationale when useful.
- **Coherence:** Resolve contradictory instructions and keep each rule beside its exceptions. Separate instructions from supplied input with headings or delimiters where confusion is possible; distinguish authoritative instructions from data.
- **Pruning:** State each meaning once, and cut any line that does not change what the executor would do by default.
