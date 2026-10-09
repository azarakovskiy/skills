---
name: meta-prompt
description: Turn a rough request into a shared, execution-ready task, then run it or write the prompt.
disable-model-invocation: true
dependencies:
  - name: grilling
    repo: mattpocock/skills
---

The text after this invocation is a task. Turn it into the minimum task brief an agent can execute without consequential guesses. A clear, low-risk request should pass quickly.

## 1. Map the decision tree

Map only gaps that could change the outcome, risk, or scope. Classify each as:

- **Fact:** discoverable from the environment.
- **Decision:** only the user can choose.
- **Free choice:** safe for the executor to choose.

The **frontier** is every decision whose prerequisites are settled. Answers can expose dependent decisions, so recompute the tree after every user response.

**Done when:** every consequential gap is classified and the current frontier is known.

## 2. Resolve the frontier

Before each round, look up only the facts needed to settle or ask the current frontier. Stop each lookup when you have the fact, a source pointer, or an explicit unknown. Carry findings forward as concise source pointers. Save implementation exploration for execution.

Run the round as a grilling session. Call the skill tool for `grilling` and follow that skill. When the skill tool cannot find `grilling`, give the user the install instruction in [dependencies.md](dependencies.md), read [grilling_fallback.md](grilling_fallback.md), and run the round from that file.

Facts are the agent's work; decisions are the user's. Free choices are defaults in the brief, not questions. After each answer, recompute the tree and run the next round. Move on only when the frontier stays empty after that recomputation.

**Done when:** the frontier is empty and no consequential decision is silently assumed.

## 3. Smart zone

The smart zone is the low-context part of the window where the model is still sharp. Quality drops as context fills, long before the advertised limit.

The task fits one pass when it has one outcome, one connected working set, and one verification loop that can stay in that zone. Split when it has independent outcomes, unrelated systems, phases that need different evidence, or enough material to crowd the task out of the zone. Propose the smallest sequence in which each pass still finishes something, and ask the user to narrow the task or approve the sequence.

**Done when:** the brief says fits or split, with the reason, and a split has an agreed boundary.

## 4. Confirm

Default to executing here. Produce a reusable prompt only when the user asks for one or corrects the default.

Present every brief with this exact template:

```markdown
## Task brief

- **Outcome:** <intended result>
- **Artifact:** <what will be created or changed>
- **Done when:** <observable evidence>
- **Boundaries:** <scope, exclusions, and permissions>
- **Context:** <source pointers and explicit unknowns>
- **Approach:** <chosen approach and executor free choices>
- **Verification:** <checks>
- **Smart zone:** <fits or split, with reason and agreed boundary if split>
- **Delivery:** <execute here or produce a prompt>

**Is this what you want?**
```

Wait for an explicit yes. A correction reshapes the decision tree: return to the frontier before presenting a revised brief.

**Done when:** the user confirms the brief.

## 5. Session

Stay when this session holds context the executor needs and its instructions match the brief. Recommend a new session when competing instructions, rejected drafts, or unrelated context would crowd the task. Exploration the executor would repeat is a reason to stay. Say the verdict and reason in one sentence.

## 6. Deliver

- **Execute here:** carry out the confirmed brief.
- **Produce a prompt:** read `write.md` and write it from the brief.
