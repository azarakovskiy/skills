# Degraded writing-for-agents pass

Treat the prompt as an agent-facing document:

- Put required actions in execution order; keep reference beside the step that uses it.
- End each step with a clear, exhaustive completion condition.
- Point to discoverable sources of truth instead of copying them.
- Co-locate each concept, its rules, and its caveats.
- Prefer compact leading words and positive instructions.
- Delete duplication, stale material, and lines that do not change agent behavior.

**Done when:** every remaining line changes execution, every meaning has one source of truth, and every required outcome has a checkable bound.

Return to the prompt-me skill.
