---
name: prompt-me
description: Turn a rough request into a confirmed, high-level task prompt — clarify what only the user can decide, advise on splitting and model, then run it here or write it.
disable-model-invocation: true
---

Turn the user's request into the prompt an expert prompt engineer would write: high-level, complete on intent, and safe to run **AFK**, with no human to ask once it starts. A clear request passes quickly.

## 1. Clarify

Check the request against [prompt-quality.md](prompt-quality.md) and find every **conceptual decision** the executor would otherwise guess: goal, scope, constraints, preferences, what done means, and any contradiction. These belong to the user; ask them now. Technical choices (approach, steps, mechanisms, files, API design, data shapes) belong to the executor, and the prompt leaves them as its call. Ask for the **outcome or limit** the user wants and leave the **mechanism** that delivers it to the executor: ask how stale the data may get rather than whether to cache it, and what a failure must never cause rather than which safeguards to build.

Look up an established fact yourself when it sharpens a question or exposes a contradiction. Carry facts into the prompt as pointers the executor checks before relying on them, not as the specifics you found.

When conceptual decisions are open, ask them in rounds as [clarify.md](clarify.md) describes.

**Done when:** no conceptual decision is left for the executor to guess, and every open technical choice is explicitly the executor's.

## 2. Brief

Present a brief that shows, in plain language, what will happen, so the user can confirm shared understanding at a glance. It fits on one screen. Give each line one sentence or a few bullets, and skip a line with nothing to say.

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

The brief says what, never how: no plan and no implementation steps.

### Fit

A **smart zone** is a low-load context where a model reliably tracks the goal, the material it must hold together, and its checks; reliability fades well before the advertised context window. Judge from what must be loaded and verified together whether the work fits one smart zone.

**Load alone decides the split.** Steps that differ in kind or suit different models share one pass, and the user switches models between them; a separate session costs the user manual work.

State a one-line verdict with its load-based reason: "Fits one pass — <reason>" or "Split into N parts — <reason>".

Under a split verdict, list each part by the outcome it delivers:

- **<outcome>** — done when <observable condition>; needs <an earlier part's output> | runs in parallel

### Model

In one sentence, nudge toward a model class (cheap, standard, frontier) and a relative effort with one task-grounded reason, for example "a frontier model on fairly high effort: reasoning through crash interleavings" or "a cheap model on low effort: three settled label edits". The nudge is the whole answer to any model question the user raised. Keep it relative; the user maps it to their lineup. Give one nudge per part or step when their needs differ.

### Next

Recommend **Run it here** when the task is small and clear, fits one pass, and this session holds nothing that would steer execution wrong: rejected designs, conflicting directions, or unrelated history. Otherwise recommend **Write the prompt(s)** and name the split or the interfering material. Honor a request for a reusable prompt.

**Done when:** the brief fits one screen, carries every settled decision, and ends with a recommended route.

## 3. Confirm

Wait for the user's reply. Choosing a route confirms the brief and authorizes that route; a plain "yes" takes the recommended one. A correction reopens the decisions it touches: return to step 1, then present the revised brief.

**Done when:** the user has confirmed the current brief and a route is chosen.

## 4. Run or write

- **Run it here:** execute the confirmed brief in this session.
- **Write the prompt(s):** follow [write.md](write.md).
