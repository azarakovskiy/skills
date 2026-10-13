# Clarification fallback

Resolve consequential gaps: unknowns that could change the goal, scope, constraints, or acceptance criteria. Model them as a **design tree**, with downstream decisions attached to the decisions or facts they require. Separate discoverable facts from user decisions; leave safe implementation choices to the executor.

## Fact discovery

Find environment facts yourself, delegating lookups to a subagent when available, and retain source pointers with the findings. A pending lookup holds back only the decisions that need its result; continue asking independent questions. Ask the user for information or access only when necessary evidence is inaccessible and actually blocks progress.

## Interview rounds

The **frontier** is the set of unresolved user decisions whose prerequisites are settled. Ask the entire frontier together, with numbered questions and a recommended answer for each. Use this format:

```text
❓ **Q1** - **<question title>**: <question body>

➡️ <recommended answer>
```

Repeat the entry for each question, increasing its number and placing `---` on its own line, with blank lines around it, between entries.

Wait for the user's answers before the next round. Incorporate answers and lookup results, reshape the design tree, and recompute the frontier. Questions that depend on another unanswered question belong in a later round, even if both could appear in the same message.

## Completion

Finish only when the frontier is empty and no consequential gaps or pending blocking facts remain. Execution-time facts may remain unknown only with an explicit lookup or check before reliance.

Return the resolved facts, source pointers, and decisions to prompt-me for fit assessment and confirmation. This fallback neither confirms the brief, chooses sessions, nor executes the task.
