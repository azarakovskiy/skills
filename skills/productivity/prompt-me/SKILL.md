---
name: prompt-me
description: Clarify a rough request into a confirmed task brief and recommend where to execute it.
disable-model-invocation: true
dependencies:
  - name: grilling
    repo: mattpocock/skills
  - name: writing-for-agents
    repo: mattpocock/skills
---

Turn the user's prompt into the minimum task brief an agent can execute without consequential guesses. A clear, low-risk request should pass quickly.

## 1. Clarify

Check the request against [prompt-quality.md](prompt-quality.md). If no consequential gaps remain, continue directly to step 2 without loading `grilling`.

When consequential gaps remain, load and run `grilling`. If unavailable, give the warning and install instruction in [dependencies.md](dependencies.md), then use [grilling_fallback.md](grilling_fallback.md).

Limit the session to gaps affecting outcome, scope, risk, or verification: ambiguous wording, missing facts or user decisions, and conflicting instructions. Leave safe implementation choices to the executor.

**Done when:** every consequential gap is resolved and the brief meets the prompt-quality checklist. Only execution-time facts with an explicit lookup or check before reliance may remain unknown.

## 2. Assess smart-zone fit

Assess whether the clarified request can be executed and verified in one **smart zone**: a low-load context where the model can reliably track the goal, constraints, evidence, and checks together. Reliability can decline before the advertised context limit; there is no universal token cutoff.

- **Fits:** recommend one pass when the outcome, connected working set, and verification loop can stay in that zone.
- **Does not fit:** recommend splitting at seams that separate context-heavy working sets, with explicit inputs and outputs between passes. Name the material that makes one pass too large and propose the smallest sequence that preserves the whole goal. Each pass must produce a verifiable result; related steps sharing the same evidence stay together.

**Done when:** the brief says fits or split with a reason, and each proposed pass has a deliverable, prerequisites, and check.

## 3. Session assessment

Stay when this session holds useful context and its instructions match the brief. Recommend a fresh session when conflicting earlier directions, rejected drafts likely to be reused, or dominant unrelated history would crowd or steer execution.

Also recommend a fresh session when resolving a vague request loaded substantial prompt-building material that execution does not need: interview scaffolding, prompt drafts, or guidance on how to write a prompt. Distinguish this from ordinary clarification that supplies useful execution facts.

Name the material that would interfere or crowd the working context; length alone is not a reason to restart.

**Done when:** the brief says here or new with a concrete reason.

## 4. Confirm

Present the brief with this template. Default to recommending a session. Choose execution only when the user explicitly asks to execute the confirmed brief; describing the task alone is not that authorization. Honor requests for a reusable prompt.

```markdown
## Task brief

- **Outcome:** <intended result>
- **Artifact:** <what will be created or changed>
- **Done when:** <observable evidence>
- **Boundaries:** <scope, exclusions, and permissions>
- **Context:** <source pointers, necessary user-provided facts, and explicit unknowns>
- **Approach:** <settled decisions and executor free choices>
- **Verification:** <checks>
- **Smart zone:** <fits or split, with reason and proposed pass boundaries>
- **Session:** <here or new, with reason>
- **Delivery:** <recommend session, execute here, or produce a prompt>

**Is this what you want?**
```

Wait for explicit confirmation of the brief and any split boundaries. A correction reopens affected gaps: return to clarification and reassess fit before presenting the revised brief.

**Done when:** the user confirms the current brief.

## 5. Deliver

After confirmation, state the session recommendation:

- **Here:** recommend continuing here. Execute only if the user also explicitly authorized execution; confirming the brief alone is not authorization.
- **New session, or reusable prompt requested:** load `writing-for-agents`, then follow [write.md](write.md). If unavailable, give the warning and install instruction in [dependencies.md](dependencies.md) and use [writing_for_agents_fallback.md](writing_for_agents_fallback.md) before writing.
