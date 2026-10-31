# Clarify in rounds

The **frontier** is every open conceptual decision whose prerequisites are settled. A decision that depends on an unanswered question or a pending lookup waits for a later round.

Ask the whole frontier in one message, numbered, with a recommendation for each:

```text
❓ **Q1** - **<question title>**: <question body>

➡️ <recommended user outcome or limit; leave delivery mechanisms to the executor>
```

Separate entries with `---` on its own line, blank lines around it.

Wait for answers, incorporate them, and recompute the frontier.

**Done when:** the frontier is empty; continue with the brief.
