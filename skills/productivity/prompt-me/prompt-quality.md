# Execution prompt quality

- **Outcome:** State the task, intended result, and concrete deliverable: what the executor should produce or change, not merely the topic.
- **Phrasing:** Use direct verbs and measurable requirements. State positive target behavior (“Return three ranked options”); pair consequential prohibitions with the desired alternative.
- **Grounding:** Supply relevant facts and resolvable pointers to authoritative sources. Require lookup or checks before relying on unknown facts; clarify consequential decisions rather than inventing assumptions.
- **Boundaries:** Specify consequential scope, exclusions, constraints, and permissions. Leave safe implementation choices open; prescribe procedures only when dependencies, safety, or correctness require them.
- **Completion and revalidation:** Define observable acceptance criteria and feasible checks. Require checking the actual result against those criteria with evidence or tools where appropriate, correcting discrepancies, and naming checks left unverified.
- **Delivery:** Specify format, audience, and examples when they change the result or resolve ambiguity. Keep examples consistent with instructions; omit them when the requirements suffice.
- **Reasoning:** Match guidance to the model and task. Reasoning models need no step-by-step prompting or private chain-of-thought disclosure; request key assumptions or a concise rationale when useful.
- **Coherence:** Resolve contradictory instructions. Separate instructions from supplied input with headings or delimiters where confusion is possible; distinguish authoritative instructions from data.
