---
name: prompt-me
description: Turn rough requests into confirmed, high-level prompts — clarify user decisions, advise on split and model, then run here or write.
disable-model-invocation: true
---

Turn the request into an expert-written prompt: high-level, intent-complete, and safe to run **AFK** without a human to ask. Clear requests pass quickly.

## 1. Clarify

Check the request against [prompt-quality.md](prompt-quality.md) and find every **conceptual decision** the executor would otherwise guess, including unstated ones: goal, scope, constraints (including operational limits), preferences, what done means, and any contradiction. These belong to the user; ask them now. Technical choices (approach, steps, mechanisms, files, API design, data shapes) belong to the executor, and the prompt leaves them as its call. Frame questions and recommendations around **what users need to do or experience**—capabilities, workflows, outcomes, limits, and product preferences—leaving the **technical interfaces and mechanisms** that deliver them to the executor: ask how stale the data may get rather than whether to cache it, and what a failure must never cause rather than which safeguards to build.

Look up established facts when they sharpen a question or expose a contradiction. Carry source pointers the executor checks before reliance, not copied specifics, into the prompt.

For open conceptual decisions, follow [clarify.md](clarify.md).

**Done when:** no conceptual decision is left for the executor to guess, and every open technical choice is explicitly the executor's.

## 2. Brief

Present what will happen in a one-screen, plain-language brief for at-a-glance confirmation. Use one sentence or a few bullets per line; omit fields with nothing to say.

```markdown
## Brief

**Status quo:** <what exists now; only when it shapes the task>
**Goal:** <the intended result>
**Decisions:**
- <scope, constraints, and preferences the user settled, in their words>
**Done when:**
- <observable conditions>
**Fit:** <one-line verdict>
**Model:** <relative nudge>

**Next:** <Run it here | Write the prompt(s)> (recommended), or <the other>.
```

What, never how: no plan or implementation steps.

### Fit

A **smart zone** is a low-load context where a model reliably tracks the goal, the material it must hold together, and its checks; reliability fades well before the advertised context window. Judge from what must be loaded and verified together whether the work fits one smart zone.

**Load alone decides the split.** Steps that differ in kind or suit different models share one pass, and the user switches models between them; a separate session costs the user manual work.

State a one-line verdict whose reason names what must be loaded and verified together: "Fits one pass — <reason>" or "Split into N parts — <reason>".

Under a split verdict, preserve the full goal; list each part by the outcome it delivers and name the earlier output any dependency requires:

- **<outcome>** — done when <observable condition>; needs <an earlier part's output> | runs in parallel

### Model

In one sentence: model class (cheap, standard, frontier), relative effort, one task-grounded reason. For example, "a frontier model on fairly high effort: reasoning through crash interleavings" or "a cheap model on low effort: three settled label edits". Keep model answers to this nudge; the user maps it to their lineup. Give one per part or step when needs differ.

### Next

Recommend **Run it here** for small, clear, one-pass work when this session has no interference (rejected designs, conflicting directions, unrelated history). Otherwise recommend **Write the prompt(s)**, naming the split or interference. Honor reusable-prompt requests.

**Done when:** the one-screen brief carries every settled decision and ends with a recommended route.

## 3. Confirm

Wait for the user's reply. A route choice confirms the brief and authorizes that route; a plain "yes" selects the recommendation. Corrections reopen affected decisions: return to step 1 and present a revised brief.

**Done when:** the user confirms the current brief and chooses a route.

## 4. Run or write

- **Run it here:** execute the confirmed brief in this session.
- **Write the prompt(s):** follow [write.md](write.md).
